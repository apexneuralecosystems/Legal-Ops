"""
Base agent class for all specialized agents.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pydantic import BaseModel, Field


class AgentMetadata(BaseModel):
    """Metadata block for agent outputs."""
    agent_id: str
    timestamp_utc: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version_tag: str = "1.0"
    human_reviewed: bool = False
    reviewer_id: Optional[str] = None


class SourceReference(BaseModel):
    """Reference to source document/segment."""
    doc_id: str
    segment_id: Optional[str] = None
    page: Optional[int] = None
    confidence: Optional[float] = None


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    
    Provides:
    - Standard input/output JSON schema validation
    - Confidence scoring framework
    - Human review flag logic
    - Source reference tracking
    - Metadata block generation
    """
    
    def __init__(self, agent_id: str):
        """
        Initialize the agent.
        
        Args:
            agent_id: Unique identifier for this agent
        """
        self.agent_id = agent_id
        self.metadata = AgentMetadata(agent_id=agent_id)
    
    @abstractmethod
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method to be implemented by each agent.
        
        Args:
            inputs: Input data dictionary
            
        Returns:
            Output data dictionary with results and metadata
        """
        pass
    
    def create_metadata(
        self,
        human_reviewed: bool = False,
        reviewer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create metadata block for output.
        
        Args:
            human_reviewed: Whether output has been human-reviewed
            reviewer_id: ID of reviewer if applicable
            
        Returns:
            Metadata dictionary
        """
        return {
            "agent_id": self.agent_id,
            "timestamp_utc": datetime.utcnow().isoformat(),
            "version_tag": "1.0",
            "human_reviewed": human_reviewed,
            "reviewer_id": reviewer_id
        }
    
    def should_escalate_to_human(
        self,
        confidence: float,
        threshold: float = 0.7
    ) -> bool:
        """
        Determine if output should be escalated for human review.
        
        Args:
            confidence: Confidence score (0.0-1.0)
            threshold: Minimum acceptable confidence
            
        Returns:
            True if human review required
        """
        return confidence < threshold
    
    def create_source_reference(
        self,
        doc_id: str,
        segment_id: Optional[str] = None,
        page: Optional[int] = None,
        confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create a source reference object.
        
        Args:
            doc_id: Document ID
            segment_id: Segment ID (optional)
            page: Page number (optional)
            confidence: Confidence score (optional)
            
        Returns:
            Source reference dictionary
        """
        ref = {"doc_id": doc_id}
        if segment_id:
            ref["segment_id"] = segment_id
        if page is not None:
            ref["page"] = page
        if confidence is not None:
            ref["confidence"] = confidence
        return ref
    
    def log_action(
        self,
        action_type: str,
        description: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        changes: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create an audit log entry.
        
        Args:
            action_type: Type of action performed
            description: Human-readable description
            entity_type: Type of entity affected
            entity_id: ID of entity affected
            changes: Dictionary of changes made
            
        Returns:
            Audit log entry dictionary
        """
        return {
            "agent_id": self.agent_id,
            "action_type": action_type,
            "action_description": description,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "changes": changes,
            "timestamp_utc": datetime.utcnow().isoformat()
        }
    
    async def validate_input(self, inputs: Dict[str, Any], required_fields: List[str]) -> None:
        """
        Validate that required input fields are present.
        
        Args:
            inputs: Input dictionary
            required_fields: List of required field names
            
        Raises:
            ValueError: If required fields are missing
        """
        missing = [field for field in required_fields if field not in inputs]
        if missing:
            raise ValueError(f"Missing required input fields: {', '.join(missing)}")
    
    def format_output(
        self,
        data: Dict[str, Any],
        confidence: Optional[float] = None,
        human_review_required: bool = False,
        status: str = "success"
    ) -> Dict[str, Any]:
        """
        Format agent output with standard structure.
        
        Args:
            data: Output data
            confidence: Overall confidence score
            human_review_required: Whether human review is needed
            status: Operation status (success/error)
            
        Returns:
            Formatted output dictionary
        """
        output = {
            "status": status,
            "data": data,
            "metadata": self.create_metadata(),
            "human_review_required": human_review_required
        }
        
        if confidence is not None:
            output["confidence"] = confidence
            
        return output
