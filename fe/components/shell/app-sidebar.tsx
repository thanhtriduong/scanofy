import {
  BookOpen,
  GraduationCap,
  Library,
  Search,
  Settings,
} from "lucide-react";

const navigation = [
  { label: "Thư viện", icon: Library, active: true, available: true },
  { label: "Tri thức", icon: BookOpen, active: false, available: false },
  { label: "Học tập", icon: GraduationCap, active: false, available: false },
];

export function AppSidebar() {
  return (
    <aside className="hidden h-screen flex-col border-r border-border bg-surface lg:sticky lg:top-0 lg:flex">
      <div className="flex h-16 items-center gap-3 border-b border-border px-5">
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-sm font-semibold text-primary-foreground">
          S
        </span>
        <div>
          <p className="text-sm font-semibold">Scanofy</p>
          <p className="text-xs text-muted-foreground">Learning workspace</p>
        </div>
      </div>

      <div className="p-3">
        <button
          type="button"
          disabled
          aria-label="Tìm kiếm — sắp có"
          className="flex h-9 w-full cursor-not-allowed items-center gap-2 scanofy-control border border-border bg-surface-raised px-3 text-sm text-muted-foreground opacity-70"
        >
          <Search className="h-4 w-4" aria-hidden="true" />
          Tìm kiếm
          <span className="ml-auto text-xs text-muted-foreground">⌘ K</span>
        </button>
      </div>

      <nav aria-label="Điều hướng chính" className="space-y-1 px-3">
        {navigation.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.label}
              type="button"
              disabled={!item.available}
              aria-current={item.active ? "page" : undefined}
              className={`flex h-9 w-full items-center gap-3 scanofy-control px-3 text-sm font-medium transition-colors ${
                item.active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground disabled:cursor-not-allowed disabled:opacity-55"
              }`}
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              {item.label}
              {!item.available && (
                <span className="ml-auto text-xs font-normal">Sắp có</span>
              )}
            </button>
          );
        })}
      </nav>

      <div className="mt-6 px-6">
        <p className="text-xs font-medium text-muted-foreground">Không gian làm việc</p>
        <div className="mt-3 flex items-center gap-3 text-sm text-foreground">
          <span className="h-2 w-2 rounded-full bg-primary" aria-hidden="true" />
          Tài liệu của tôi
        </div>
      </div>

      <div className="mt-auto border-t border-border p-3">
        <button
          type="button"
          disabled
          aria-label="Cài đặt — sắp có"
          className="flex h-9 w-full cursor-not-allowed items-center gap-3 scanofy-control px-3 text-sm text-muted-foreground opacity-70"
        >
          <Settings className="h-4 w-4" aria-hidden="true" />
          Cài đặt
        </button>
      </div>
    </aside>
  );
}
