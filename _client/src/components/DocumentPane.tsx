import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useRunFile } from "../api/queries";
import { useSaveFile } from "../api/mutations";

interface DocumentPaneProps {
  slug: string;
  file: string;
}

type ViewMode = "edit" | "preview";

export function DocumentPane({ slug, file }: DocumentPaneProps) {
  const isDirectory = file.endsWith("/");
  const query = useRunFile(slug, isDirectory ? undefined : file);
  const save = useSaveFile(slug, file);
  const [draft, setDraft] = useState("");
  const [dirty, setDirty] = useState(false);
  const [mode, setMode] = useState<ViewMode>("edit");

  useEffect(() => {
    if (query.data && !dirty) {
      setDraft(query.data.content);
    }
  }, [query.data, dirty]);

  if (isDirectory) {
    return (
      <p className="document-pane__notice">
        This stage's output is a folder ({file}) — no single-file viewer yet.
      </p>
    );
  }

  if (query.isLoading) return <p>Loading {file}...</p>;
  if (query.isError) return <p role="alert">Could not load {file}.</p>;

  return (
    <div className="document-pane">
      <div className="document-pane__toolbar">
        <div className="document-pane__label mono">{file}</div>
        <div className="document-pane__tabs" role="tablist" aria-label="Document view">
          <button
            type="button"
            role="tab"
            aria-selected={mode === "edit"}
            className={`document-pane__tab${mode === "edit" ? " document-pane__tab--active" : ""}`}
            onClick={() => setMode("edit")}
          >
            Edit
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "preview"}
            className={`document-pane__tab${mode === "preview" ? " document-pane__tab--active" : ""}`}
            onClick={() => setMode("preview")}
          >
            Preview
          </button>
        </div>
      </div>

      {mode === "edit" ? (
        <div className="document-pane__editor">
          <textarea
            value={draft}
            onChange={(event) => {
              setDraft(event.target.value);
              setDirty(true);
            }}
          />
        </div>
      ) : (
        <div className="document-pane__editor document-pane__editor--preview">
          <div className="document-pane__markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{draft}</ReactMarkdown>
          </div>
        </div>
      )}

      <div className="document-pane__actions">
        <button
          className="btn btn--ghost"
          onClick={() => save.mutate(draft, { onSuccess: () => setDirty(false) })}
          disabled={!dirty || save.isPending}
        >
          {save.isPending ? "Saving…" : "Save"}
        </button>
      </div>
    </div>
  );
}
