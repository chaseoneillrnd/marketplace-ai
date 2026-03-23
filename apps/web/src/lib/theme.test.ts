import { describe, it, expect } from 'vitest';
import { DARK, LIGHT } from './theme';
import tokens from '../../../../design/tokens.json';

describe('Theme — admin panel tokens', () => {
  describe('DARK theme', () => {
    it('has adminBg with exact value', () => {
      expect(DARK.adminBg).toBe('#060e1a');
    });
    it('has adminSurfaceSide with exact value', () => {
      expect(DARK.adminSurfaceSide).toBe('#0a1520');
    });
    it('has purpleDim with exact value', () => {
      expect(DARK.purpleDim).toBe('rgba(167,139,250,0.12)');
    });
  });

  describe('LIGHT theme', () => {
    it('has adminBg with exact value', () => {
      expect(LIGHT.adminBg).toBe('#e8eef6');
    });
    it('has adminSurfaceSide with exact value', () => {
      expect(LIGHT.adminSurfaceSide).toBe('#f5f8fc');
    });
    it('has purpleDim with exact value', () => {
      expect(LIGHT.purpleDim).toBe('rgba(109,79,212,0.09)');
    });
  });
});

describe('tokens.json — admin panel additions', () => {
  it('has layout.adminSidebarWidth', () => {
    expect(tokens.layout.adminSidebarWidth).toBe('240px');
  });
  it('has layout.queueListWidth', () => {
    expect(tokens.layout.queueListWidth).toBe('380px');
  });

  it('has transitions.drag', () => {
    expect(tokens.transitions.drag).toBe('0.2s');
  });

  describe('borders section', () => {
    it('has navActiveIndicator', () => {
      expect((tokens as any).borders.navActiveIndicator).toBe('3px');
    });
    it('has focus', () => {
      expect((tokens as any).borders.focus).toBe('2px');
    });
    it('has input', () => {
      expect((tokens as any).borders.input).toBe('1px');
    });
  });

  describe('chart section', () => {
    it('has seriesOrder as an array of 6 colors', () => {
      expect((tokens as any).chart.seriesOrder).toEqual([
        '#4b7dff',
        '#a78bfa',
        '#1fd49e',
        '#f2a020',
        '#ef5060',
        '#22d3ee',
      ]);
    });
    it('has axisText referencing muted', () => {
      expect((tokens as any).chart.axisText).toBe('muted');
    });
    it('has gridLine referencing border', () => {
      expect((tokens as any).chart.gridLine).toBe('border');
    });
    it('has chartBg referencing surface', () => {
      expect((tokens as any).chart.chartBg).toBe('surface');
    });
  });
});

// ---------- WCAG AA Contrast Helpers ----------

/** sRGB channel → linear */
function linearize(c: number): number {
  const s = c / 255;
  return s <= 0.04045 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
}

/** Relative luminance per WCAG 2.x */
function relativeLuminance(hex: string): number {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b);
}

/** Contrast ratio between two hex colors */
function contrastRatio(hex1: string, hex2: string): number {
  const l1 = relativeLuminance(hex1);
  const l2 = relativeLuminance(hex2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

describe('Theme — WCAG AA contrast (light mode)', () => {
  const AA_NORMAL = 4.5; // minimum for normal text

  it('LIGHT.green achieves >= 4.5:1 contrast on white (#ffffff)', () => {
    expect(contrastRatio(LIGHT.green, '#ffffff')).toBeGreaterThanOrEqual(AA_NORMAL);
  });

  it('LIGHT.amber achieves >= 4.5:1 contrast on white (#ffffff)', () => {
    expect(contrastRatio(LIGHT.amber, '#ffffff')).toBeGreaterThanOrEqual(AA_NORMAL);
  });

  it('LIGHT.green achieves >= 4.5:1 contrast on LIGHT.surface', () => {
    expect(contrastRatio(LIGHT.green, LIGHT.surface)).toBeGreaterThanOrEqual(AA_NORMAL);
  });

  it('LIGHT.amber achieves >= 4.5:1 contrast on LIGHT.bg (#f0f4f9)', () => {
    expect(contrastRatio(LIGHT.amber, LIGHT.bg)).toBeGreaterThanOrEqual(AA_NORMAL);
  });

  it('LIGHT.greenDim is an rgba string', () => {
    expect(LIGHT.greenDim).toMatch(/^rgba\(/);
  });

  it('LIGHT.amberDim is an rgba string', () => {
    expect(LIGHT.amberDim).toMatch(/^rgba\(/);
  });

  it('DARK.green is unchanged (#1fd49e)', () => {
    expect(DARK.green).toBe('#1fd49e');
  });

  it('DARK.amber is unchanged (#f2a020)', () => {
    expect(DARK.amber).toBe('#f2a020');
  });
});

describe('Theme — adminSidebarWidth token', () => {
  it('DARK has adminSidebarWidth', () => {
    expect(DARK.adminSidebarWidth).toBe('240px');
  });
  it('LIGHT has adminSidebarWidth', () => {
    expect(LIGHT.adminSidebarWidth).toBe('240px');
  });
});
