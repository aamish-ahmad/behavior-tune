# Global runtime manifest

BehaviorTune uses the installed global Codex runtime. The runtime is not vendored
here.

| Required global skill | Resolution path |
| --- | --- |
| `trajectory-prompt-compiler` | `C:\\Users\\chuwi\\.codex\\skills\\trajectory-prompt-compiler\\SKILL.md` |
| `bounded-executor` | `C:\\Users\\chuwi\\.codex\\skills\\bounded-executor\\SKILL.md` |
| `transition-commit-gate` | `C:\\Users\\chuwi\\.codex\\skills\\transition-commit-gate\\SKILL.md` |

G3-A resolved these paths before implementation. This project-local manifest is
a pointer and boundary record, not a runtime implementation.
