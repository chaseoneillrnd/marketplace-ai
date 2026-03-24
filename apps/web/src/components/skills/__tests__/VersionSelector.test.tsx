import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { VersionSelector } from '../VersionSelector';
import type { VersionItem } from '../../../hooks/useSkillVersions';

const VERSIONS: VersionItem[] = [
  {
    id: 'v1-id',
    version: '2.0.0',
    changelog: 'Major update',
    published_at: '2026-03-20T00:00:00Z',
  },
  {
    id: 'v2-id',
    version: '1.0.0',
    changelog: 'Initial release',
    published_at: '2026-03-10T00:00:00Z',
  },
];

describe('VersionSelector', () => {
  it('renders all versions in the dropdown', () => {
    render(
      <VersionSelector
        slug="my-skill"
        currentVersion="2.0.0"
        versions={VERSIONS}
        onSelect={vi.fn()}
      />,
    );
    expect(screen.getByTestId('version-selector')).toBeInTheDocument();
    const dropdown = screen.getByTestId('version-dropdown') as HTMLSelectElement;
    expect(dropdown.options).toHaveLength(2);
  });

  it('highlights the current version with "(Current)" badge', () => {
    render(
      <VersionSelector
        slug="my-skill"
        currentVersion="2.0.0"
        versions={VERSIONS}
        onSelect={vi.fn()}
      />,
    );
    const dropdown = screen.getByTestId('version-dropdown') as HTMLSelectElement;
    const currentOption = Array.from(dropdown.options).find((o) => o.value === '2.0.0');
    expect(currentOption?.textContent).toContain('(Current)');

    const otherOption = Array.from(dropdown.options).find((o) => o.value === '1.0.0');
    expect(otherOption?.textContent).not.toContain('(Current)');
  });

  it('calls onSelect when a different version is chosen', () => {
    const onSelect = vi.fn();
    render(
      <VersionSelector
        slug="my-skill"
        currentVersion="2.0.0"
        versions={VERSIONS}
        onSelect={onSelect}
      />,
    );
    const dropdown = screen.getByTestId('version-dropdown');
    fireEvent.change(dropdown, { target: { value: '1.0.0' } });
    expect(onSelect).toHaveBeenCalledWith('1.0.0');
  });

  it('renders with the current version selected by default', () => {
    render(
      <VersionSelector
        slug="my-skill"
        currentVersion="2.0.0"
        versions={VERSIONS}
        onSelect={vi.fn()}
      />,
    );
    const dropdown = screen.getByTestId('version-dropdown') as HTMLSelectElement;
    expect(dropdown.value).toBe('2.0.0');
  });
});
