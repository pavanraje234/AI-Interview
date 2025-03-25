def generate_report(candidate_name, role, candidate_score, posture_score, eye_score):
    """Generates a PDF report comparing the candidate's performance with others, including posture and eye contact scores."""
    role_scores = role_scores()
    scores_for_role = role_scores.get(role, [])

    if not scores_for_role:
        avg_score = 0
    else:
        avg_score = sum(scores_for_role) / len(scores_for_role)

    total_candidates = sum(len(scores) for scores in role_scores.values())
    candidates_in_role = len(scores_for_role)

    # Bar Chart: Candidate vs. Average Score
    plt.figure(figsize=(6, 4))
    plt.bar(["Candidate", "Average"], [candidate_score, avg_score], color=["blue", "green"])
    plt.xlabel("Comparison")
    plt.ylabel("Score")
    plt.title(f"Candidate vs. Average Score for {role}")
    score_chart_path = f"{REPORTS_FOLDER}/{candidate_name}_score_chart.png"
    plt.savefig(score_chart_path)
    plt.close()

    # Histogram: Score Distribution for the Role
    plt.figure(figsize=(6, 4))
    bins = min(len(scores_for_role), 5)
    plt.hist(scores_for_role, bins=bins, color="purple", alpha=0.7, edgecolor="black")
    plt.axvline(candidate_score, color="red", linestyle="dashed", linewidth=2, label="Candidate")
    plt.text(candidate_score + 0.5, 0.5, f" {candidate_score}", color="red", fontsize=10, verticalalignment="bottom")
    plt.xticks(range(min(scores_for_role), max(scores_for_role) + 1))
    plt.xlabel("Score Range")
    plt.ylabel("Number of Candidates")
    plt.title(f"Score Distribution for {role}")
    plt.legend()
    score_distribution_path = f"{REPORTS_FOLDER}/{candidate_name}_score_distribution.png"
    plt.savefig(score_distribution_path)
    plt.close()

    # Generate PDF Report
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, f"Interview Report - {candidate_name}", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Role: {role}", ln=True)
    pdf.cell(0, 10, f"Candidate's Final Score: {candidate_score}/100", ln=True)
    pdf.cell(0, 10, f"Posture Score: {posture_score}/10", ln=True)
    pdf.cell(0, 10, f"Eye Contact Score: {eye_score}/10", ln=True)
    pdf.cell(0, 10, f"Average Score for {role}: {avg_score:.2f}/100", ln=True)
    pdf.cell(0, 10, f"Total Candidates: {total_candidates}", ln=True)
    pdf.cell(0, 10, f"Candidates for {role}: {candidates_in_role}", ln=True)
    pdf.ln(10)

    # Add the bar chart
    pdf.cell(0, 10, "Candidate vs. Average Score:", ln=True)
    pdf.image(score_chart_path, x=40, w=130)
    pdf.ln(10)

    # Add the histogram
    pdf.cell(0, 10, "Score Distribution for Role:", ln=True)
    pdf.image(score_distribution_path, x=40, w=130)
    pdf.ln(10)

    pdf.cell(0, 10, "End of Report", ln=True, align="C")

    # Save the PDF
    report_path = f"{REPORTS_FOLDER}/{candidate_name}_report.pdf"
    pdf.output(report_path)
    print(f"Report generated: {report_path}")
    
    # **Delete the images after adding them to the PDF**
    try:
        os.remove(score_chart_path)
        os.remove(score_distribution_path)
        print("Temporary chart images deleted successfully.")
    except Exception as e:
        print(f"Error deleting chart images: {e}")

    return report_path
