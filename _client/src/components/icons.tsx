import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function base(props: IconProps) {
  return {
    width: 16,
    height: 16,
    viewBox: "0 0 20 20",
    fill: "none" as const,
    xmlns: "http://www.w3.org/2000/svg",
    "aria-hidden": true,
    ...props,
  };
}

export function IconCheck(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M4 10.5L8 14.5L16 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconCheckCircle(props: IconProps) {
  return (
    <svg {...base(props)}>
      <circle cx="10" cy="10" r="7.2" stroke="currentColor" strokeWidth="1.6" />
      <path d="M6.8 10.2L9 12.4L13.4 7.6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconLock(props: IconProps) {
  return (
    <svg {...base(props)}>
      <rect x="5.5" y="9" width="9" height="7" rx="1.4" stroke="currentColor" strokeWidth="1.5" />
      <path d="M7.2 9V6.8a2.8 2.8 0 0 1 5.6 0V9" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

export function IconChevronDown(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M5 7.5L10 12.5L15 7.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconChevronRight(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M7.5 5L12.5 10L7.5 15" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconPlus(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M10 4V16M4 10H16" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

export function IconSend(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M10 15V5M10 5L5.5 9.5M10 5L14.5 9.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconChat(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path
        d="M4 5.5h12a1 1 0 0 1 1 1V13a1 1 0 0 1-1 1H9l-3.2 2.6c-.4.3-.9 0-.9-.5V14H4a1 1 0 0 1-1-1V6.5a1 1 0 0 1 1-1Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function IconPencil(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12.5 4.5l3 3L7 16H4v-3l8.5-8.5Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}

export function IconBook(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path
        d="M4 5.2c1.6-.8 3.6-.8 5.2 0v10c-1.6-.8-3.6-.8-5.2 0V5.2ZM15.2 5.2c-1.6-.8-3.6-.8-5.2 0v10c1.6-.8 3.6-.8 5.2 0V5.2Z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function IconFolder(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path
        d="M3.5 6.2c0-.7.6-1.2 1.2-1.2h3l1.4 1.6h6.2c.7 0 1.2.5 1.2 1.2v6.5c0 .7-.5 1.2-1.2 1.2H4.7c-.7 0-1.2-.5-1.2-1.2V6.2Z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function IconFile(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path
        d="M6.5 3.5h5l3 3v10a1 1 0 0 1-1 1h-7a1 1 0 0 1-1-1v-12a1 1 0 0 1 1-1Z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
      <path d="M11.5 3.5V6.5a1 1 0 0 0 1 1H15.5" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
    </svg>
  );
}

export function IconWrench(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path
        d="M13.5 4.8a3 3 0 0 0-4 3.7L4.8 13.2a1.4 1.4 0 0 0 2 2l4.7-4.7a3 3 0 0 0 3.7-4l-2 2-1.7-.3-.3-1.7 2.3-2.3Z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function IconAlertTriangle(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M10 4.2 17 15.8H3L10 4.2Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="M10 8.5V11.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="10" cy="13.6" r="0.7" fill="currentColor" />
    </svg>
  );
}

export function IconColumns(props: IconProps) {
  return (
    <svg {...base(props)}>
      <rect x="4" y="4.5" width="5" height="11" rx="1" stroke="currentColor" strokeWidth="1.4" />
      <rect x="11" y="4.5" width="5" height="11" rx="1" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}

export function toolIcon(name: string, props: IconProps = {}) {
  if (name === "write_file" || name === "edit_file") return <IconPencil {...props} />;
  if (name === "read_file") return <IconBook {...props} />;
  if (name === "create_run") return <IconFolder {...props} />;
  if (name === "mark_ready_for_review") return <IconCheckCircle {...props} />;
  return <IconWrench {...props} />;
}
