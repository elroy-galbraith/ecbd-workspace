interface DiffViewProps {
  diff: string;
}

export function DiffView({ diff }: DiffViewProps) {
  const lines = diff.split("\n");
  return (
    <pre className="diff-view">
      {lines.map((line, index) => {
        let className = "diff-view__line";
        if (line.startsWith("+") && !line.startsWith("+++")) className += " diff-view__line--added";
        else if (line.startsWith("-") && !line.startsWith("---")) className += " diff-view__line--removed";
        return (
          <div key={index} className={className}>
            {line}
          </div>
        );
      })}
    </pre>
  );
}
