import os
import csv
import io
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.experiment import Experiment, ExperimentRun, TestCaseRun
from app.models.project import Project
from app.models.dataset import Dataset

REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "generated_reports"))
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_csv_report(db: Session, experiment_id: int) -> str:
    """Generate a comprehensive CSV report for an experiment."""
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise ValueError(f"Experiment {experiment_id} not found.")

    filename = f"evalforge_report_exp_{exp.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(REPORTS_DIR, filename)

    runs = db.query(ExperimentRun).filter(ExperimentRun.experiment_id == exp.id).all()

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["EvalForge Experiment Benchmark Report"])
        writer.writerow(["Experiment ID", exp.id])
        writer.writerow(["Experiment Name", exp.name])
        writer.writerow(["Project ID", exp.project_id])
        writer.writerow(["Status", exp.status])
        writer.writerow(["Started At", exp.started_at])
        writer.writerow(["Completed At", exp.completed_at])
        writer.writerow([])

        # Header for detailed cases
        writer.writerow([
            "Run ID", "Model Name", "Case ID", "Query / Input", "Expected Output",
            "Generated Output", "Status", "Latency (ms)", "Input Tokens", "Output Tokens",
            "Cost ($)", "Evaluations (Metric:Score:Passed)"
        ])

        for run in runs:
            case_runs = db.query(TestCaseRun).filter(TestCaseRun.experiment_run_id == run.id).all()
            for cr in case_runs:
                eval_strs = [
                    f"{ev.metric_name}:{ev.score:.2f}:{'PASS' if ev.passed else 'FAIL'}"
                    for ev in cr.evaluations
                ]
                writer.writerow([
                    run.id,
                    run.model_name,
                    cr.dataset_case_id or "",
                    cr.input_text.replace("\n", " ") if cr.input_text else "",
                    cr.expected_output.replace("\n", " ") if cr.expected_output else "",
                    cr.generated_output.replace("\n", " ") if cr.generated_output else "",
                    cr.status,
                    cr.latency_ms,
                    cr.input_tokens,
                    cr.output_tokens,
                    cr.cost_estimate,
                    "; ".join(eval_strs)
                ])

    return filepath

def generate_pdf_report(db: Session, experiment_id: int) -> str:
    """Generate an executive PDF report using ReportLab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise ValueError(f"Experiment {experiment_id} not found.")

    proj = db.query(Project).filter(Project.id == exp.project_id).first()
    dataset = db.query(Dataset).filter(Dataset.id == exp.dataset_id).first() if exp.dataset_id else None

    filename = f"evalforge_report_exp_{exp.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        alignment=0
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#2563eb"),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155")
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b")
    )

    story = []

    # Title & Header
    story.append(Paragraph("<b>EvalForge</b> – LLM Evaluation & Benchmark Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", body_style))
    story.append(Spacer(1, 12))

    # Executive Summary Table
    meta_data = [
        [Paragraph("<b>Experiment:</b>", body_style), Paragraph(exp.name, body_style),
         Paragraph("<b>Status:</b>", body_style), Paragraph(exp.status.upper(), body_style)],
        [Paragraph("<b>Project:</b>", body_style), Paragraph(proj.name if proj else "N/A", body_style),
         Paragraph("<b>Dataset:</b>", body_style), Paragraph(dataset.name if dataset else "N/A", body_style)],
        [Paragraph("<b>Started:</b>", body_style), Paragraph(str(exp.started_at)[:19] if exp.started_at else "N/A", body_style),
         Paragraph("<b>Completed:</b>", body_style), Paragraph(str(exp.completed_at)[:19] if exp.completed_at else "N/A", body_style)],
    ]
    meta_table = Table(meta_data, colWidths=[90, 180, 90, 180])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Model Performance Comparison Table
    story.append(Paragraph("Model Benchmark Comparison", heading_style))
    runs = db.query(ExperimentRun).filter(ExperimentRun.experiment_id == exp.id).all()

    model_headers = [
        Paragraph("<b>Model</b>", table_cell),
        Paragraph("<b>Correctness</b>", table_cell),
        Paragraph("<b>Faithfulness</b>", table_cell),
        Paragraph("<b>Relevance</b>", table_cell),
        Paragraph("<b>Avg Latency</b>", table_cell),
        Paragraph("<b>Total Tokens</b>", table_cell),
        Paragraph("<b>Est. Cost</b>", table_cell),
        Paragraph("<b>Success</b>", table_cell),
    ]
    model_rows = [model_headers]

    best_model = None
    best_score = -1.0

    for r in runs:
        m = r.summary_metrics or {}
        correctness = m.get("avg_correctness", 0.0)
        if correctness > best_score:
            best_score = correctness
            best_model = r.model_name

        model_rows.append([
            Paragraph(r.model_name, table_cell),
            Paragraph(f"{correctness*100:.1f}%", table_cell),
            Paragraph(f"{m.get('avg_faithfulness', 0.0)*100:.1f}%", table_cell),
            Paragraph(f"{m.get('avg_relevance', 0.0)*100:.1f}%", table_cell),
            Paragraph(f"{m.get('avg_latency_ms', 0.0):.1f} ms", table_cell),
            Paragraph(f"{m.get('total_tokens', 0):,}", table_cell),
            Paragraph(f"${m.get('total_cost', 0.0):.4f}", table_cell),
            Paragraph(f"{m.get('success_count', 0)}/{m.get('success_count',0)+m.get('fail_count',0)}", table_cell),
        ])

    comp_table = Table(model_rows, colWidths=[110, 60, 65, 60, 65, 65, 55, 60])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 14))

    # Recommendations & Engineering Insights
    story.append(Paragraph("Evaluator Findings & Recommendations", heading_style))
    recs = [
        f"• <b>Primary Model Recommendation:</b> <b>{best_model or 'N/A'}</b> demonstrated highest ground truth fidelity ({best_score*100:.1f}% accuracy).",
        "• <b>Grounding Analysis:</b> Review failed test cases where hallucination scores fell below the 0.80 benchmark threshold.",
        "• <b>Cost vs Latency Optimization:</b> If deploying in latency-critical production, consider model routing where simpler classification queries use fast models.",
        "• <b>Observability:</b> All test executions retain trace identifiers in EvalForge for full span-level inspection."
    ]
    for rec in recs:
        story.append(Paragraph(rec, body_style))
        story.append(Spacer(1, 4))

    doc.build(story)
    return filepath
