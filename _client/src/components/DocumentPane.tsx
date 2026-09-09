import { useEffect, useState } from "react";
import { useRunFile } from "../api/queries";
import { useSaveFile } from "../api/mutations";

interface DocumentPaneProps {
  slug: string;
  file: string;
}

export function DocumentPane({ slug, file }: DocumentPaneProps) {
  const isDirectory = file.endsWith("/");
  const query = useRunFile(slug, isDirectory ? undefined : file);
  const save = useSaveFile(slug, file);
  const [draft, setDraft] = useState("");
  const [dirty, setDirty] = useState(false);

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
      <div className="document-pane__label">{file}</div>
      <textarea
        value={draft}
        onChange={(event) => {
          setDraft(event.target.value);
          setDirty(true);
        }}
      />
      <button
        onClick={() => save.mutate(draft, { onSuccess: () => setDirty(false) })}
        disabled={!dirty || save.isPending}
      >
        {save.isPending ? "Saving…" : "Save"}
      </button>
    </div>
  );
}
