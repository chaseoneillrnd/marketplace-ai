import type { VersionItem } from '../../hooks/useSkillVersions';

interface VersionSelectorProps {
  slug: string;
  currentVersion: string;
  versions: VersionItem[];
  onSelect: (version: string) => void;
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

export function VersionSelector({ slug, currentVersion, versions, onSelect }: VersionSelectorProps) {
  return (
    <div data-testid="version-selector" className="version-selector">
      <label htmlFor={`version-select-${slug}`} className="sr-only">
        Select version
      </label>
      <select
        id={`version-select-${slug}`}
        data-testid="version-dropdown"
        value={currentVersion}
        onChange={(e) => onSelect(e.target.value)}
        aria-label="Select skill version"
      >
        {versions.map((v) => (
          <option key={v.id} value={v.version}>
            {v.version}
            {v.version === currentVersion ? ' (Current)' : ''}
            {' — '}
            {v.published_at ? formatDate(v.published_at) : ''}
          </option>
        ))}
      </select>
    </div>
  );
}
