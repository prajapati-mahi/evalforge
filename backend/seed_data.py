import asyncio
from datetime import datetime, timezone, timedelta
from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.user import User
from app.models.project import Project
from app.models.dataset import Dataset, DatasetCase
from app.models.prompt import Prompt, PromptVersion
from app.models.provider import ModelProviderKey, ModelPricing
from app.models.experiment import Experiment, ExperimentRun, TestCaseRun
from app.models.evaluation import EvaluationResult
from app.models.trace import Trace, TraceSpan
from app.core.pricing import DEFAULT_PRICING_TABLE

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Create or get Demo User
        user = db.query(User).filter(User.email == "demo@evalforge.dev").first()
        if not user:
            user = User(
                email="demo@evalforge.dev",
                hashed_password=get_password_hash("evalforge123"),
                full_name="Alex Rivera (Lead AI Engineer)",
                role="developer",
                is_active=True,
                is_superuser=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created demo user: {user.email}")
        else:
            print(f"Demo user exists: {user.email}")

        # 2. Seed Default Model Pricing
        for model_name, info in DEFAULT_PRICING_TABLE.items():
            existing_p = db.query(ModelPricing).filter(ModelPricing.model_name == model_name).first()
            if not existing_p:
                p = ModelPricing(
                    provider=info["provider"],
                    model_name=model_name,
                    input_price_per_1m=info["input_price_per_1m"],
                    output_price_per_1m=info["output_price_per_1m"],
                    effective_date=info["effective_date"],
                    is_custom=False
                )
                db.add(p)
        db.commit()

        # 3. Demo Provider Keys (Mock provider marked default)
        mock_key = db.query(ModelProviderKey).filter(ModelProviderKey.user_id == user.id, ModelProviderKey.provider_name == "mock").first()
        if not mock_key:
            mock_key = ModelProviderKey(
                user_id=user.id,
                provider_name="mock",
                key_prefix="mock-engine",
                encrypted_key="mock-key-operational",
                is_active=True,
                is_default=True
            )
            db.add(mock_key)
            db.commit()

        # 4. Create Demo Project
        project = db.query(Project).filter(Project.owner_id == user.id, Project.name == "[DEMO] Financial Advisory RAG").first()
        if not project:
            project = Project(
                name="[DEMO] Financial Advisory RAG",
                description="Production benchmarking project testing grounding, faithfulness, and latency for automated financial portfolio QA.",
                project_type="rag",
                default_model="mock-gpt-4o",
                owner_id=user.id
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            print(f"Created demo project: {project.name}")

        # 5. Create Demo Dataset
        dataset = db.query(Dataset).filter(Dataset.project_id == project.id).first()
        if not dataset:
            dataset = Dataset(
                project_id=project.id,
                name="[DEMO] SEC 10-K Q&A Grounding Set",
                description="Audited evaluation dataset with retrieved SEC 10-K earnings report filings.",
                version=1,
                num_cases=5,
                file_format="jsonl"
            )
            db.add(dataset)
            db.commit()
            db.refresh(dataset)

            cases_data = [
                {
                    "input_text": "What was Apple's total net sales in Fiscal 2023 according to their 10-K?",
                    "expected_output": "Apple's total net sales in Fiscal 2023 were $383.29 billion.",
                    "context": "Form 10-K Apple Inc. Item 7: Net sales was $383,285 million in 2023 compared to $394,328 million in 2022, a decrease of 3%. Services revenue reached an all-time record of $85.2 billion.",
                    "metadata": {"ticker": "AAPL", "year": 2023}
                },
                {
                    "input_text": "Did Microsoft's Intelligent Cloud segment revenue grow in FY23?",
                    "expected_output": "Yes, Intelligent Cloud revenue grew 17% to $87.9 billion in FY23.",
                    "context": "Microsoft Annual Report FY23: Intelligent Cloud revenue was $87.9 billion and increased 17%, driven by Azure and other cloud services revenue growth of 27%.",
                    "metadata": {"ticker": "MSFT", "year": 2023}
                },
                {
                    "input_text": "What risk factors did NVIDIA cite regarding export restrictions on high-end GPUs?",
                    "expected_output": "NVIDIA cited US government licensing requirements that impact shipments of A100 and H100 integrated circuits to China and certain other countries.",
                    "context": "NVIDIA Form 10-K: The US government announced interim final rules impacting shipments of our A100, A800, H100, H800, and L40S products to China and countries in Groups D1, D4, and D5.",
                    "metadata": {"ticker": "NVDA", "year": 2023}
                },
                {
                    "input_text": "What is the Fed's primary interest rate mechanism according to FOMC notes?",
                    "expected_output": "The Federal Open Market Committee sets the target range for the federal funds rate as its primary policy tool.",
                    "context": "Federal Reserve Monetary Policy Report: The Committee judges that the stance of monetary policy is in restrictive territory, setting the federal funds target range at 5.25 to 5.50 percent.",
                    "metadata": {"topic": "macroeconomics"}
                },
                {
                    "input_text": "What caused the decline in Alphabet's advertising revenue in late 2022?",
                    "expected_output": "A pullback in advertiser spending due to macroeconomic headwinds and tough prior-year comparisons.",
                    "context": "Alphabet Inc. Q4 2022 Earnings: Google advertising revenues were $59.0 billion, down 3.6% year-over-year, impacted by cautious advertiser spend amidst inflationary pressures.",
                    "metadata": {"ticker": "GOOGL", "year": 2022}
                }
            ]

            saved_cases = []
            for cd in cases_data:
                c = DatasetCase(
                    dataset_id=dataset.id,
                    input_text=cd["input_text"],
                    expected_output=cd["expected_output"],
                    context=cd["context"],
                    metadata_json=cd["metadata"]
                )
                db.add(c)
                saved_cases.append(c)
            db.commit()

        # 6. Create Demo Prompt & Versions
        prompt = db.query(Prompt).filter(Prompt.project_id == project.id).first()
        if not prompt:
            prompt = Prompt(
                project_id=project.id,
                name="Financial Analyst Synthesizer",
                description="Zero-shot grounded extraction prompt for SEC 10-K passages.",
                current_version=2
            )
            db.add(prompt)
            db.commit()
            db.refresh(prompt)

            pv1 = PromptVersion(
                prompt_id=prompt.id,
                version_number=1,
                template_text="Context: {{context}}\n\nQuestion: {{input}}\n\nAnswer:",
                system_instruction="You are a financial analyst. Answer directly based on the context.",
                variables=["context", "input"],
                model_parameters={"temperature": 0.5, "max_tokens": 512},
                change_summary="Baseline prompt template"
            )
            pv2 = PromptVersion(
                prompt_id=prompt.id,
                version_number=2,
                template_text="[OFFICIAL SEC FILING CONTEXT]\n{{context}}\n\n[INQUIRY]\n{{input}}\n\nProvide an exact, factually substantiated answer citing numbers accurately. If unknown, state clearly.",
                system_instruction="You are an audited compliance and financial analyst. Refuse to extrapolate beyond facts.",
                variables=["context", "input"],
                model_parameters={"temperature": 0.2, "max_tokens": 512},
                change_summary="Enhanced compliance grounding instructions"
            )
            db.add(pv1)
            db.add(pv2)
            db.commit()

        # 7. Create Demo Experiment & Runs & Traces
        exp = db.query(Experiment).filter(Experiment.project_id == project.id).first()
        if not exp:
            exp = Experiment(
                project_id=project.id,
                name="[DEMO] Multi-Model Grounding & Latency Benchmark",
                description="Comparative multi-model evaluation testing mock-gpt-4o vs mock-claude-3-5-sonnet on SEC 10-K dataset.",
                status="completed",
                dataset_id=dataset.id,
                prompt_version_id=prompt.id,
                config_json={
                    "models": ["mock-gpt-4o", "mock-claude-3-5-sonnet", "mock-gemini-1.5-pro"],
                    "evaluators": ["correctness", "faithfulness", "context_precision", "context_recall", "response_relevance", "hallucination"],
                    "temperature": 0.2,
                    "max_tokens": 512
                },
                created_by=user.id,
                started_at=datetime.now(timezone.utc) - timedelta(hours=2),
                completed_at=datetime.now(timezone.utc) - timedelta(hours=1, minutes=45),
                total_cases=15,
                processed_cases=15
            )
            db.add(exp)
            db.commit()
            db.refresh(exp)

            models_config = [
                {"name": "mock-gpt-4o", "provider": "mock", "c_rate": 0.94, "f_rate": 0.96, "lat": 380.0, "cost": 0.0035},
                {"name": "mock-claude-3-5-sonnet", "provider": "mock", "c_rate": 0.91, "f_rate": 0.95, "lat": 440.0, "cost": 0.0042},
                {"name": "mock-gemini-1.5-pro", "provider": "mock", "c_rate": 0.88, "f_rate": 0.90, "lat": 290.0, "cost": 0.0018},
            ]

            cases = db.query(DatasetCase).filter(DatasetCase.dataset_id == dataset.id).all()

            for mc in models_config:
                run = ExperimentRun(
                    experiment_id=exp.id,
                    model_name=mc["name"],
                    provider_name=mc["provider"],
                    status="completed",
                    summary_metrics={
                        "avg_correctness": mc["c_rate"],
                        "avg_faithfulness": mc["f_rate"],
                        "avg_context_precision": round(mc["f_rate"] - 0.04, 2),
                        "avg_context_recall": round(mc["c_rate"] - 0.02, 2),
                        "avg_relevance": 0.95,
                        "avg_hallucination_score": round(mc["f_rate"] + 0.02, 2),
                        "avg_latency_ms": mc["lat"],
                        "total_tokens": 1450,
                        "total_cost": mc["cost"],
                        "success_count": len(cases),
                        "fail_count": 0
                    },
                    started_at=datetime.now(timezone.utc) - timedelta(hours=2),
                    completed_at=datetime.now(timezone.utc) - timedelta(hours=1, minutes=50)
                )
                db.add(run)
                db.commit()
                db.refresh(run)

                for c in cases:
                    cr = TestCaseRun(
                        experiment_run_id=run.id,
                        dataset_case_id=c.id,
                        input_text=c.input_text,
                        expected_output=c.expected_output,
                        context=c.context,
                        generated_output=f"According to the official filing context, {c.expected_output}",
                        status="success",
                        latency_ms=mc["lat"] + 15,
                        input_tokens=180,
                        output_tokens=65,
                        total_tokens=245,
                        cost_estimate=round(mc["cost"] / len(cases), 6),
                        retry_count=0
                    )
                    db.add(cr)
                    db.commit()
                    db.refresh(cr)

                    # Add evaluation results
                    for m_name, score in [
                        ("correctness", mc["c_rate"]),
                        ("faithfulness", mc["f_rate"]),
                        ("context_precision", mc["f_rate"] - 0.04),
                        ("context_recall", mc["c_rate"] - 0.02),
                        ("response_relevance", 0.95),
                        ("hallucination", mc["f_rate"] + 0.02)
                    ]:
                        ev = EvaluationResult(
                            test_case_run_id=cr.id,
                            metric_name=m_name,
                            score=round(score, 2),
                            passed=score >= 0.70,
                            reasoning=f"[DEMO]: Model demonstrated robust grounding score of {score:.2f} adhering to SEC disclosure bounds.",
                            supported_claims=[c.expected_output],
                            unsupported_claims=[],
                            evidence=c.context[:120],
                            latency_ms=18.5
                        )
                        db.add(ev)
                    db.commit()

                    # Add Trace & Nested Spans
                    trace = Trace(
                        project_id=project.id,
                        experiment_id=exp.id,
                        test_case_run_id=cr.id,
                        trace_name=f"trace_{mc['name']}_case_{c.id}",
                        status="success",
                        start_time=datetime.now(timezone.utc) - timedelta(minutes=50),
                        end_time=datetime.now(timezone.utc) - timedelta(minutes=49),
                        latency_ms=mc["lat"],
                        total_tokens=245,
                        total_cost=round(mc["cost"] / len(cases), 6),
                        metadata_json={"model": mc["name"], "case_id": c.id, "environment": "demo"}
                    )
                    db.add(trace)
                    db.commit()
                    db.refresh(trace)

                    # Span 1: Retrieval
                    s1 = TraceSpan(
                        trace_id=trace.id,
                        span_name="Vector Retrieval (10-K Chunks)",
                        span_type="retrieval",
                        start_time=trace.start_time,
                        latency_ms=45.0,
                        input_data=c.input_text,
                        output_data=c.context[:150],
                        status="success",
                        attributes_json={"top_k": 3, "similarity_threshold": 0.82}
                    )
                    db.add(s1)

                    # Span 2: Generation
                    s2 = TraceSpan(
                        trace_id=trace.id,
                        span_name=f"Inference: {mc['name']}",
                        span_type="model_generation",
                        start_time=trace.start_time + timedelta(milliseconds=50),
                        latency_ms=mc["lat"],
                        input_data=c.input_text,
                        output_data=cr.generated_output,
                        status="success",
                        attributes_json={"tokens": 245, "temperature": 0.2}
                    )
                    db.add(s2)

                    # Span 3: Evaluation
                    s3 = TraceSpan(
                        trace_id=trace.id,
                        span_name="Evaluator Engine (RAG Triad)",
                        span_type="evaluation",
                        start_time=trace.start_time + timedelta(milliseconds=mc["lat"] + 60),
                        latency_ms=65.0,
                        input_data=cr.generated_output,
                        output_data="Evaluated 6 metrics; overall pass",
                        status="success",
                        attributes_json={"metrics": ["correctness", "faithfulness", "relevance"]}
                    )
                    db.add(s3)
                    db.commit()

            print("Database seeded with comprehensive demo project, dataset, prompt, benchmark runs, and traces!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
