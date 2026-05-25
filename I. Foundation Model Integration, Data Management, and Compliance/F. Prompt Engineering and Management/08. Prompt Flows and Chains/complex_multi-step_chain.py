from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableParallel
import json

model = ChatBedrock(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    model_kwargs={"temperature": 0}
)

fast_model = ChatBedrock(
    model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
    model_kwargs={"temperature": 0}
)

class DocumentProcessingChain:
    """Multi-step document processing workflow."""

    def __init__(self):
        self.build_chain()

    def build_chain(self):
        """Build the complete processing chain."""

        # Step 1: Extract metadata (fast model)
        metadata_prompt = ChatPromptTemplate.from_template(
            """Extract metadata from this document:
            {document}

            Return JSON with: title, author (if found), date (if found), type (article/report/email/other)"""
        )

        # Step 2: Generate summary (main model)
        summary_prompt = ChatPromptTemplate.from_template(
            """Summarize this {doc_type} in 3-4 sentences:
            {document}"""
        )

        # Step 3: Extract entities (parallel with summary)
        entities_prompt = ChatPromptTemplate.from_template(
            """Extract all named entities from:
            {document}

            Return JSON with: people, organizations, locations, dates"""
        )

        # Step 4: Generate keywords
        keywords_prompt = ChatPromptTemplate.from_template(
            """Based on this summary and entities, generate 5 relevant keywords.

            Summary: {summary}
            Entities: {entities}

            Return as comma-separated list."""
        )

        # Step 5: Quality check
        quality_prompt = ChatPromptTemplate.from_template(
            """Review this document analysis for quality and completeness.

            Original document type: {doc_type}
            Summary: {summary}
            Keywords: {keywords}

            Is this analysis complete and accurate? Respond with:
            {{"quality": "good" or "needs_review", "issues": [] or ["issue1", "issue2"]}}"""
        )

        # Build the chain
        self.chain = (
            # Start with document
            RunnablePassthrough.assign(
                # Step 1: Extract metadata
                metadata=lambda x: self._parse_json(
                    (metadata_prompt | fast_model | StrOutputParser()).invoke(x)
                )
            )
            | RunnablePassthrough.assign(
                doc_type=lambda x: x.get("metadata", {}).get("type", "document")
            )
            # Steps 2 & 3: Parallel processing
            | RunnablePassthrough.assign(
                summary=summary_prompt | model | StrOutputParser(),
                entities=lambda x: self._parse_json(
                    (entities_prompt | fast_model | StrOutputParser()).invoke(x)
                )
            )
            # Step 4: Generate keywords
            | RunnablePassthrough.assign(
                keywords=keywords_prompt | model | StrOutputParser()
            )
            # Step 5: Quality check
            | RunnablePassthrough.assign(
                quality_check=lambda x: self._parse_json(
                    (quality_prompt | model | StrOutputParser()).invoke(x)
                )
            )
            # Format final output
            | RunnableLambda(self._format_output)
        )

    def _parse_json(self, text):
        """Safely parse JSON from text."""
        try:
            # Try to extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
        except:
            return {"raw": text}

    def _format_output(self, data):
        """Format the final output."""
        return {
            "metadata": data.get("metadata", {}),
            "summary": data.get("summary", ""),
            "entities": data.get("entities", {}),
            "keywords": [k.strip() for k in data.get("keywords", "").split(",")],
            "quality": data.get("quality_check", {})
        }

    def process(self, document):
        """Process a document through the chain."""
        return self.chain.invoke({"document": document})


# Example usage
processor = DocumentProcessingChain()

document = """
AWS Announces New Generative AI Features for Amazon Bedrock

SEATTLE, January 2024 - Amazon Web Services (AWS) today announced several
new features for Amazon Bedrock, including improved prompt management,
enhanced model evaluation capabilities, and new Claude 3 model integrations.

The new Prompt Management feature allows developers to version, test, and
deploy prompts independently of application code, reducing deployment risk
and enabling faster iteration.

"These enhancements represent a significant step forward in making generative
AI more accessible and manageable for enterprise customers," said Dr. Swami
Sivasubramanian, Vice President of AI and Data at AWS.

The features are available starting today in US East (N. Virginia) and will
roll out to additional regions over the coming weeks.
"""

result = processor.process(document)
print(json.dumps(result, indent=2))