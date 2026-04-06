import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from nexus_core.llm_provider import create_llm_client
import asyncio

from nexus_core.models import CompileIntentRequest, CompileIntentResponse, ExecuteSearchRequest, SearchResponse
from nexus_core.logger import get_logger
from nexus_core.stealth import stealth_ddg_search, ghost_protocol, CircuitBreakerExc
from nexus_core.agents import auto_refine_intent, run_dork_orchestrator, run_judge, run_analyst, run_scribe
from nexus_core.intelligence import find_hidden_github_email
from nexus_core.safety import pii_scrubber
from nexus_core.utils import safe_int, detect_platform, sanitize_html

logger = get_logger("nexus_api")

app = FastAPI(title="NEXUS V3 API", description="B2B Prospecting Engine Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "🟢 Online", "service": "NEXUS Core Backend"}

@app.post("/api/v1/compile-intent", response_model=CompileIntentResponse)
async def compile_intent(req: CompileIntentRequest):
    logger.info(f"Extracting intelligence from Omni-Prompt")
    try:
        client = OpenAI(api_key=req.api_key, base_url="https://models.inference.ai.azure.com")
        
        extracted_schema = auto_refine_intent(client, req.model_choice, req.omni_prompt)
        
        dorks = run_dork_orchestrator(client, req.model_choice, extracted_schema)
        
        platform_dorks = {
            "LinkedIn": f"site:linkedin.com/in/ {dorks.get('linkedin', '')}",
            "GitHub": f"site:github.com {dorks.get('github', '')}",
            "News/Twitter": f"{dorks.get('news', '')}"
        }
        
        logger.info("Intelligence extraction successful")
        return CompileIntentResponse(
            extracted_schema=extracted_schema,
            platform_dorks=platform_dorks
        )
        
    except Exception as e:
        logger.error(f"Intelligence extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/execute-search", response_model=SearchResponse)

async def execute_search(req: ExecuteSearchRequest):
    logger.info("Executing Omni-Vector Search Phase")
    try:
        ghost_protocol.check_circuit()
    except CircuitBreakerExc as e:
        logger.warning(f"Circuit Breaker tripped: {e}")
        return SearchResponse(raw_leads_count=0, qualified_leads_count=0, qualified_leads=[], error=str(e))

    raw_leads = []
    seen_urls = set()
    
    # Harvest
    for platform_name, dork in req.platform_dorks.items():
        if not dork.strip() or dork.strip() in ["site:linkedin.com/in/", "site:github.com"]:
            continue
            
        logger.info(f"Targeting {platform_name} with Vector: {dork}")
        try:
            results = stealth_ddg_search(dork, max_results=req.max_results)
            for r in results:
                u = r.get("URL", "")
                if u and u not in seen_urls:
                    seen_urls.add(u)
                    r["Platform"] = platform_name
                    raw_leads.append(r)
        except Exception as e:
            logger.error(f"Vector search bypass for {platform_name}: {e}")
            continue

    if not raw_leads:
        return SearchResponse(raw_leads_count=0, qualified_leads_count=0, qualified_leads=[], error="Direct Vector Match Failure. Loosen Omni-Prompt constraints.")

    # Judge & Enrich
    client = create_llm_client(
    provider=req.provider,
    api_key=req.api_key
    )  
    qualified_leads = []
    
    for lead in raw_leads:
        try:
            safe_title = pii_scrubber(lead.get("Title", ""))
            safe_snippet = pii_scrubber(lead.get("Snippet", ""))
            lead["Title"] = sanitize_html(safe_title)
            lead["Snippet"] = sanitize_html(safe_snippet)

            verdict = run_judge(client, req.model_choice, lead, req.extracted_schema)
            
            if verdict.get("Status", "REJECTED").upper() == "APPROVED":
                lead["Match_Score"] = safe_int(verdict.get("Composite", 0))
                lead["Pain_Point_Match"] = safe_int(verdict.get("Pain_Point_Match", 0))
                
                # Deep Pivot
                found_platform = detect_platform(lead.get("URL", ""))
                try:
                    if found_platform == "GitHub" or 'github.com' in lead.get("URL", ""):
                        email_data = find_hidden_github_email(lead["URL"], client, req.model_choice, req.api_key)
                        lead["Validated_Email"] = email_data.get("email") if email_data.get("email") else email_data.get("status")
                    else:
                        lead["Validated_Email"] = "N/A"
                except Exception as e:
                    logger.warning(f"Graceful degradation on enrichment: {e}")
                    lead["Validated_Email"] = "N/A"
                
                # Scribe Writer
                try:
                    lead["COPY_Pitch"] = run_scribe(client, req.model_choice, lead, req.compiled_params)
                except Exception as e:
                    logger.warning(f"Graceful degradation on Scribe: {e}")
                    lead["COPY_Pitch"] = "N/A"
                    
                qualified_leads.append(lead)
            else:
                logger.debug(f"Judge Rejected Lead: {verdict.get('Reason')}")
                
        except Exception as e:
            logger.error(f"Error processing lead {lead.get('URL', '')}: {e}")
            continue
            
    logger.info(f"Validation complete. {len(qualified_leads)} B2B prospects qualified.")
    return SearchResponse(
        raw_leads_count=len(raw_leads),
        qualified_leads_count=len(qualified_leads),
        qualified_leads=qualified_leads
    )
