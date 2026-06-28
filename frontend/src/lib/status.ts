/** Maps backend status strings to a Badge tone + display label. */

export function resumeStatusBadge(status: string): { tone: "neutral" | "accent" | "success" | "warning" | "danger"; label: string } {
  switch (status) {
    case "uploaded":
      return { tone: "neutral", label: "uploaded" };
    case "extracting":
    case "analyzing":
      return { tone: "accent", label: status };
    case "extracted":
    case "analyzed":
      return { tone: "accent", label: status };
    case "failed":
      return { tone: "danger", label: "failed" };
    default:
      return { tone: "neutral", label: status };
  }
}

export function portfolioStatusBadge(status: string): { tone: "neutral" | "accent" | "success" | "warning" | "danger"; label: string } {
  switch (status) {
    case "generating":
      return { tone: "accent", label: "generating" };
    case "draft":
      return { tone: "warning", label: "draft" };
    case "published":
      return { tone: "success", label: "published" };
    case "failed":
      return { tone: "danger", label: "failed" };
    default:
      return { tone: "neutral", label: status };
  }
}
