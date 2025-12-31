"""
Orchestration controller using LangGraph for workflow management.
"""
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph
import logging
from agents import (
    DocumentCollectorAgent,
    OCRLanguageAgent,
    TranslationAgent,
    CaseStructuringAgent,
    RiskScoringAgent,
    IssuePlannerAgent,
    TemplateComplianceAgent,
    MalayDraftingAgent,
    EnglishCompanionAgent,
    ConsistencyQAAgent,
    ResearchAgent,
    ArgumentBuilderAgent,
    TranslationCertificationAgent,
    EvidenceBuilderAgent,
    HearingPrepAgent
)
import asyncio

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict, total=False):
    """State object passed between agents in workflow."""
    files: List[Dict[str, Any]]
    connector_type: str
    metadata: Dict[str, Any]
    matter_id: str
    workflow_status: str
    document_manifest: List[Dict]
    total_documents: int
    all_segments: List[Dict]
    total_page_count: int  # Added for OCR node
    parallel_texts: List[Dict]
    matter_snapshot: Dict[str, Any]
    risk_scores: Dict[str, Any]
    
    # Drafting workflow state
    template_id: str
    issues_selected: List[Dict]
    prayers_selected: List[Dict]
    planned_issues: Dict[str, Any]
    template_info: Dict[str, Any]
    pleading_ms: Dict[str, Any]
    pleading_en: Dict[str, Any]
    qa_report: Dict[str, Any]
    
    # Research workflow state
    query: str
    filters: Dict[str, Any]
    cases: List[Dict]
    argument_memo: Dict[str, Any]
    data_source: str  # "commonlii" or "mock"
    live_data: bool  # True if from CommonLII
    
    # Evidence workflow state
    documents: List[Dict]
    translation_cert: Dict[str, Any]
    evidence_packet: Dict[str, Any]
    hearing_bundle: Dict[str, Any]
    user_deadline: str  # Added for risk scoring
    pleadings: List[Dict]  # Added for evidence/hearing workflows
    issues: List[Dict]  # Added for hearing prep
    translations: List[Dict]  # Added for evidence workflow
    affidavits: List[Dict]  # Added for evidence workflow



class OrchestrationController:
    """
    Orchestrates multi-agent workflows for legal document processing.
    
    Workflows:
    - intake: Document → OCR → Translation → Case Structuring → Risk Scoring
    - draft_pleading: Issue Planning → Template → Malay Drafting → English Companion → QA
    - research: Research → Argument Building
    - evidence: Translation Cert → Evidence Builder → Hearing Prep
    """
    
    def __init__(self):
        # Initialize all agents
        self.doc_collector = DocumentCollectorAgent()
        self.ocr_agent = OCRLanguageAgent()
        self.translation_agent = TranslationAgent()
        self.case_structuring_agent = CaseStructuringAgent()
        self.risk_scoring_agent = RiskScoringAgent()
        
        # Drafting workflow agents
        self.issue_planner_agent = IssuePlannerAgent()
        self.template_compliance_agent = TemplateComplianceAgent()
        self.malay_drafting_agent = MalayDraftingAgent()
        self.english_companion_agent = EnglishCompanionAgent()
        self.consistency_qa_agent = ConsistencyQAAgent()
        
        # Research workflow agents
        self.research_agent = ResearchAgent()
        self.argument_builder_agent = ArgumentBuilderAgent()
        
        # Evidence workflow agents
        self.translation_cert_agent = TranslationCertificationAgent()
        self.evidence_builder_agent = EvidenceBuilderAgent()
        self.hearing_prep_agent = HearingPrepAgent()
        
        # Build workflow graphs
        self.intake_workflow = self._build_intake_workflow()
        self.drafting_workflow = self._build_drafting_workflow()
        self.research_workflow = self._build_research_workflow()
        self.evidence_workflow = self._build_evidence_workflow()
    
    def _build_intake_workflow(self) -> StateGraph:
        """Build the intake workflow graph."""
        
        workflow = StateGraph(WorkflowState)
        
        # Define nodes (agent steps)
        workflow.add_node("collect_documents", self._collect_documents_node)
        workflow.add_node("ocr_and_language", self._ocr_and_language_node)
        workflow.add_node("translate", self._translate_node)
        workflow.add_node("structure_case", self._structure_case_node)
        workflow.add_node("score_risk", self._score_risk_node)
        
        # Define edges (workflow sequence)
        workflow.set_entry_point("collect_documents")
        workflow.add_edge("collect_documents", "ocr_and_language")
        workflow.add_edge("ocr_and_language", "translate")
        workflow.add_edge("translate", "structure_case")
        workflow.add_edge("structure_case", "score_risk")
        workflow.set_finish_point("score_risk")
        
        return workflow.compile()
    
    def _build_drafting_workflow(self) -> StateGraph:
        """Build the drafting workflow graph."""
        
        workflow = StateGraph(WorkflowState)
        
        # Define nodes for all 5 drafting agents
        workflow.add_node("plan_issues", self._plan_issues_node)
        workflow.add_node("select_template", self._select_template_node)
        workflow.add_node("draft_malay", self._draft_malay_node)
        workflow.add_node("draft_english", self._draft_english_node)
        workflow.add_node("qa_check", self._qa_check_node)
        
        # Conditional routing based on template language
        def route_after_template(state: WorkflowState) -> str:
            """Route to appropriate drafting node based on template."""
            template_id = state.get("template_id", "TPL-HighCourt-MS-v2")
            
            # Check if English template
            if "EN" in template_id or "English" in template_id:
                return "draft_english"  # Skip Malay, go straight to English
            else:
                return "draft_malay"  # Malaysian template, draft in Malay first
        
        # Define edges (workflow sequence with conditional routing)
        workflow.set_entry_point("plan_issues")
        workflow.add_edge("plan_issues", "select_template")
        
        # Conditional routing after template selection
        workflow.add_conditional_edges(
            "select_template",
            route_after_template,
            {
                "draft_malay": "draft_malay",
                "draft_english": "draft_english"
            }
        )
        
        # If Malay drafting was done, create English companion
        workflow.add_edge("draft_malay", "draft_english")
        
        # Both paths lead to QA check
        workflow.add_edge("draft_english", "qa_check")
        workflow.set_finish_point("qa_check")
        
        return workflow.compile()
    
    def _build_research_workflow(self) -> StateGraph:
        """Build the research workflow graph."""
        
        workflow = StateGraph(WorkflowState)
        
        workflow.add_node("search_cases", self._search_cases_node)
        workflow.add_node("build_argument", self._build_argument_node)
        
        workflow.set_entry_point("search_cases")
        workflow.add_edge("search_cases", "build_argument")
        workflow.set_finish_point("build_argument")
        
        return workflow.compile()
    
    def _build_evidence_workflow(self) -> StateGraph:
        """Build the evidence workflow graph."""
        
        workflow = StateGraph(WorkflowState)
        
        workflow.add_node("certify_translation", self._certify_translation_node)
        workflow.add_node("build_packet", self._build_packet_node)
        workflow.add_node("prepare_hearing", self._prepare_hearing_node)
        
        workflow.set_entry_point("certify_translation")
        workflow.add_edge("certify_translation", "build_packet")
        workflow.add_edge("build_packet", "prepare_hearing")
        workflow.set_finish_point("prepare_hearing")
        
        return workflow.compile()
    
    async def run_intake_workflow(
        self,
        files: List[Dict[str, Any]],
        connector_type: str,
        metadata: Dict[str, Any],
        matter_id: str
    ) -> Dict[str, Any]:
        """Run the complete intake workflow."""
        
        initial_state = {
            "files": files,
            "connector_type": connector_type,
            "metadata": metadata,
            "matter_id": matter_id,
            "workflow_status": "started"
        }
        
        try:
            logger.info(f"Starting intake workflow for matter {matter_id} with {len(files)} files")
            result = await self.intake_workflow.ainvoke(initial_state)
            result["workflow_status"] = "completed"
            logger.info(f"Intake workflow completed successfully for matter {matter_id}")
            return result
        except Exception as e:
            logger.error(f"Intake workflow FAILED for matter {matter_id}: {str(e)}", exc_info=True)
            import traceback
            traceback.print_exc()  # Print full stack trace to console
            return {
                "workflow_status": "failed",
                "error": str(e),
                "matter_id": matter_id
            }
    
    async def run_drafting_workflow(
        self,
        matter_snapshot: Dict[str, Any],
        template_id: str,
        issues_selected: List[Dict],
        prayers_selected: List[Dict]
    ) -> Dict[str, Any]:
        """Run the drafting workflow."""
        
        initial_state = {
            "matter_snapshot": matter_snapshot,
            "template_id": template_id,
            "issues_selected": issues_selected,
            "prayers_selected": prayers_selected,
            "workflow_status": "started"
        }
        
        try:
            result = await self.drafting_workflow.ainvoke(initial_state)
            result["workflow_status"] = "completed"
            return result
        except Exception as e:
            return {
                "workflow_status": "failed",
                "error": str(e)
            }
    
    async def run_research_workflow(
        self,
        query: str,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run the research workflow."""
        
        initial_state = {
            "query": query,
            "filters": filters,
            "workflow_status": "started"
        }
        
        try:
            result = await self.research_workflow.ainvoke(initial_state)
            result["workflow_status"] = "completed"
            return result
        except Exception as e:
            return {
                "workflow_status": "failed",
                "error": str(e)
            }

    async def build_argument_only(
        self,
        cases: List[Dict],
        issues: List[Dict],
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run only the argument builder step."""
        
        # Manually invoke the node logic
        state = {
            "cases": cases,
            "issues_selected": issues,
            "query": query,
            "workflow_status": "started"
        }
        
        try:
            result = await self._build_argument_node(state)
            return result
        except Exception as e:
            return {
                "error": str(e)
            }
    
    async def run_evidence_workflow(
        self,
        matter_id: str,
        documents: List[Dict]
    ) -> Dict[str, Any]:
        """Run the evidence workflow."""
        
        import logging
        from database import SessionLocal
        from models import Matter, Document
        from models.pleading import Pleading
        
        logger = logging.getLogger(__name__)
        
        # Fetch contextual data from DB
        db = SessionLocal()
        pleadings_data = []
        matter_snapshot = None
        issues = []
        
        try:
            matter = db.query(Matter).filter(Matter.id == matter_id).first()
            if matter:
                matter_snapshot = matter.to_dict()
                issues = matter.issues or []
            
            pleadings = db.query(Pleading).filter(Pleading.matter_id == matter_id).all()
            pleadings_data = [p.to_dict() for p in pleadings]
        except Exception as e:
            logger.error(f"Error fetching contextual data for evidence workflow: {e}")
        finally:
            db.close()
        
        # Initialize with comprehensive defaults to prevent NoneType errors
        initial_state = {
            "matter_id": matter_id,
            "documents": documents if documents is not None else [],
            "workflow_status": "started",
            # Add defaults for all fields that might be accessed
            "pleadings": pleadings_data,
            "translations": [],
            "affidavits": [],
            "matter_snapshot": matter_snapshot,
            "evidence_packet": {},
            "cases": [],
            "issues": issues
        }
        
        try:
            logger.info(f"Starting evidence workflow for matter {matter_id} with {len(initial_state['documents'])} documents")
            result = await self.evidence_workflow.ainvoke(initial_state)
            result["workflow_status"] = "completed"
            logger.info(f"Evidence workflow completed successfully")
            return result
        except Exception as e:
            logger.error(f"Evidence workflow failed: {e}", exc_info=True)
            return {
                "workflow_status": "failed",
                "error": str(e)
            }
    
    # Node implementations
    
    async def _collect_documents_node(self, state: WorkflowState) -> WorkflowState:
        """Document collection node."""
        result = await self.doc_collector.process({
            "connector_type": state["connector_type"],
            "files": state["files"],
            "metadata": state.get("metadata", {}),
            "matter_id": state["matter_id"]
        })
        
        state["document_manifest"] = result["data"]["document_manifest"]
        state["total_documents"] = result["data"]["total_documents"]
        return state
    
    async def _ocr_and_language_node(self, state: WorkflowState) -> WorkflowState:
        """OCR and language detection node."""
        all_segments = []
        total_page_count = 0  # Track total pages across all documents
        
        for doc in state.get("document_manifest", []):
            # Prepare input for OCR agent
            ocr_input = {
                "doc_id": doc["doc_id"],
                "file_content": doc.get("file_content"),
                "mime_type": doc["mime_type"]
            }
            
            try:
                # Call OCR agent
                logger.debug(f"Calling OCR agent for {doc['doc_id']}, content_len={len(ocr_input['file_content']) if ocr_input['file_content'] else 0}")
                result = await self.ocr_agent.process(ocr_input)
                logger.debug(f"OCR agent result status: {result.get('status')}")
                
                # Collect segments
                if result.get("status") == "success":
                    segments = result["data"]["segments"]
                    logger.debug(f"OCR agent returned {len(segments)} segments")
                    all_segments.extend(segments)
                    
                    # Track actual page count from this document
                    doc_page_count = result["data"].get("actual_page_count", 1)
                    total_page_count += doc_page_count
                    logger.debug(f"Document has {doc_page_count} pages")
            except Exception as e:
                logger.error(f"OCR processing error: {e}")
                logger.error(f"OCR processing error for {doc['doc_id']}: {e}", exc_info=True)
                
        state["all_segments"] = all_segments
        state["total_page_count"] = total_page_count  # Pass total pages to next nodes
        return state
    
    async def _translate_node(self, state: WorkflowState) -> WorkflowState:
        """Translation node - optimized for speed.
        
        For intake workflow, we pass segments through directly as parallel texts
        since case structuring can work with the original text.
        Translation is skipped to avoid slow API calls for every segment.
        """
        parallel_texts = []
        
        # Instead of translating each segment (slow), pass through as parallel texts
        # with the original text serving as both source and target
        for segment in state.get("all_segments", []):
            text = segment.get("text", "")
            lang = segment.get("lang", "unknown")
            
            parallel_texts.append({
                "src": text,
                "src_lang": lang,
                "tgt_literal": text,  # Same text for now - translation can be done later if needed
                "tgt_idiom": text,
                "alignment_score": 1.0,
                "human_review": False,
                "segment_id": segment.get("segment_id"),
                "doc_id": segment.get("doc_id"),
                "page": segment.get("page"),
                "ocr_confidence": segment.get("ocr_confidence", 1.0)
            })
        
        logger.info(f"Translation node: Passed through {len(parallel_texts)} segments as parallel texts")
        state["parallel_texts"] = parallel_texts
        return state

    
    async def _structure_case_node(self, state: WorkflowState) -> WorkflowState:
        """Case structuring node."""
        result = await self.case_structuring_agent.process({
            "parallel_texts": state.get("parallel_texts", []),
            "document_manifest": state.get("document_manifest", []),
            "matter_id": state["matter_id"],
            "actual_page_count": state.get("total_page_count", 0)  # Pass actual page count
        })
        
        state["matter_snapshot"] = result["data"]["matter_snapshot"]
        return state
    
    async def _score_risk_node(self, state: WorkflowState) -> WorkflowState:
        """Risk scoring node."""
        result = await self.risk_scoring_agent.process({
            "matter_snapshot": state["matter_snapshot"],
            "document_manifest": state.get("document_manifest", []),
            "user_deadline": state.get("user_deadline")
        })
        
        state["risk_scores"] = result["data"]["risk_scores"]
        return state
    
    # Drafting workflow nodes
    
    async def _plan_issues_node(self, state: WorkflowState) -> WorkflowState:
        """Issue planning node."""
        result = await self.issue_planner_agent.process({
            "matter_snapshot": state["matter_snapshot"],
            "issues_selected": state.get("issues_selected", [])
        })
        state["planned_issues"] = result["data"]
        
        # Auto-select all issues and prayers for the automated workflow
        if not state.get("issues_selected"):
            state["issues_selected"] = result["data"].get("issues", [])
        
        if not state.get("prayers_selected"):
            state["prayers_selected"] = result["data"].get("suggested_prayers", [])
            
        return state
    
    async def _select_template_node(self, state: WorkflowState) -> WorkflowState:
        """Template selection node."""
        matter = state["matter_snapshot"]
        result = await self.template_compliance_agent.process({
            "template_id": state.get("template_id", "TPL-HighCourt-MS-v2"),
            "matter_snapshot": matter,
            "jurisdiction": matter.get("jurisdiction", "Peninsular Malaysia"),
            "court": matter.get("court", "High Court"),
            "matter_type": matter.get("case_type", "general")
        })
        state["template_info"] = result["data"]
        return state
    
    async def _draft_malay_node(self, state: WorkflowState) -> WorkflowState:
        """Malay drafting node."""
        result = await self.malay_drafting_agent.process({
            "matter_snapshot": state["matter_snapshot"],
            "template_id": state.get("template_id", "TPL-HighCourt-MS-v2"),
            "issues_selected": state.get("issues_selected", []),
            "prayers_selected": state.get("prayers_selected", [])
        })
        
        state["pleading_ms"] = result["data"]
        return state
    
    async def _draft_english_node(self, state: WorkflowState) -> WorkflowState:
        """English companion draft node."""
        
        # Check if we have Malay pleading (came from Malay-first workflow)
        if "pleading_ms" in state and state["pleading_ms"]:
            # Translate from Malay to English
            pleading_ms_data = state["pleading_ms"]
            result = await self.english_companion_agent.process({
                "pleading_ms_text": pleading_ms_data["pleading_ms_text"],
                "paragraph_map": pleading_ms_data.get("paragraph_map", []),
                "matter_snapshot": state["matter_snapshot"]
            })
            state["pleading_en"] = result["data"]
        else:
            # No Malay text - draft directly in English
            # Use the Malay drafting agent's logic but with English prompt
            result = await self.malay_drafting_agent.process({
                "matter_snapshot": state["matter_snapshot"],
                "template_id": state.get("template_id", "TPL-HighCourt-EN-v2"),
                "issues_selected": state.get("issues_selected", []),
                "prayers_selected": state.get("prayers_selected", []),
                "language": "en"  # Override to English
            })
            
            # Store in both pleading_ms AND pleading_en for consistency
            # (Frontend expects pleading_ms for now)
            state["pleading_ms"] = result["data"]
            state["pleading_en"] = {
                "pleading_en_text": result["data"]["pleading_ms_text"],
                "aligned_pairs": [],
                "divergence_flags": []
            }
        
        return state
    
    async def _qa_check_node(self, state: WorkflowState) -> WorkflowState:
        """QA check node."""
        pleading_ms_data = state["pleading_ms"]
        pleading_en_data = state["pleading_en"]
        
        result = await self.consistency_qa_agent.process({
            "pleading_ms": pleading_ms_data["pleading_ms_text"],
            "pleading_en": pleading_en_data["pleading_en_text"],
            "aligned_pairs": pleading_en_data.get("aligned_pairs", [])
        })
        state["qa_report"] = result["data"]
        return state
    
    # Research workflow nodes
    
    async def _search_cases_node(self, state: WorkflowState) -> WorkflowState:
        """Search cases node - now with CommonLII integration!"""
        result = await self.research_agent.process({
            "query": state["query"],
            "filters": state.get("filters", {})
        })
        
        # Extract cases and metadata from research agent
        data = result.get("data", {})
        state["cases"] = data.get("cases", [])
        
        # Pass through CommonLII integration metadata
        state["data_source"] = data.get("data_source", "mock")
        state["live_data"] = data.get("live_data", False)
        
        return state
    
    async def _build_argument_node(self, state: WorkflowState) -> WorkflowState:
        """Build argument node."""
        # Safely get cases and issues, ensuring they're lists
        cases = state.get("cases", [])
        issues = state.get("issues_selected", [])
        query = state.get("query")
        
        # Ensure they're actually lists, not None
        if cases is None:
            cases = []
        if issues is None:
            issues = []
            
        result = await self.argument_builder_agent.process({
            "cases": cases,
            "issues": issues,
            "query": query
        })
        state["argument_memo"] = result["data"]
        return state
    
    # Evidence workflow nodes
    
    async def _certify_translation_node(self, state: WorkflowState) -> WorkflowState:
        """Translation certification node."""
        logger.debug("Executing _certify_translation_node")
        result = await self.translation_cert_agent.process({
            "source_documents": state.get("documents", []),
            "target_language": "en"  # Defaulting to English for certification
        })
        # Safely access data
        state["translation_cert"] = result.get("data", {}) if result else {}
        logger.debug("_certify_translation_node completed")
        return state
    
    async def _build_packet_node(self, state: WorkflowState) -> WorkflowState:
        """Evidence packet builder node."""
        logger.debug("Executing _build_packet_node")
        result = await self.evidence_builder_agent.process({
            "matter_id": state["matter_id"],
            "documents": state.get("documents", []),
            "pleadings": state.get("pleadings", []),
            "translations": state.get("translations", []),
            "affidavits": state.get("affidavits", [])
        })
        # Safely access data
        state["evidence_packet"] = result.get("data", {}) if result else {}
        logger.debug("_build_packet_node completed")
        return state
    
    async def _prepare_hearing_node(self, state: WorkflowState) -> WorkflowState:
        """Hearing prep node."""
        # Get matter info from state
        matter_id = state.get("matter_id", "unknown")
        
        # Robustly get matter_snapshot (handle missing key OR None value)
        matter_snapshot = state.get("matter_snapshot")
        if not matter_snapshot:
            matter_snapshot = {"title": f"Matter {matter_id}"}
        
        result = await self.hearing_prep_agent.process({
            "matter_snapshot": matter_snapshot,
            "evidence_packet": state.get("evidence_packet", {}),
            "pleadings": state.get("pleadings", []),
            "cases": state.get("cases", []),
            "issues": state.get("issues", [])
        })
        # Safely access data
        state["hearing_bundle"] = result.get("data", {}) if result else {}
        return state
