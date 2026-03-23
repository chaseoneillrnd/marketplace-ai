import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { createElement } from 'react';
import { SparkLine } from './SparkLine';

vi.mock('recharts', async () => {
  const mod = await import('../../__mocks__/recharts');
  return mod;
});

describe('SparkLine', () => {
  it('renders without crashing', () => {
    render(createElement(SparkLine, { data: [], color: '#fff' }));
    expect(screen.getByTestId('sparkline')).toBeInTheDocument();
  });

  it('renders with data', () => {
    const data = [{ value: 1 }, { value: 2 }, { value: 3 }];
    render(createElement(SparkLine, { data, color: '#4b7dff' }));
    expect(screen.getByTestId('sparkline')).toBeInTheDocument();
  });

  it('has correct testid', () => {
    render(createElement(SparkLine, { data: [{ value: 5 }], color: '#000' }));
    expect(screen.getByTestId('sparkline')).toBeInTheDocument();
  });
});
