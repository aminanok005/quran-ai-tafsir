import { fireEvent, render, screen, within } from '@testing-library/react';
import { SuggestedFollowUps } from './SuggestedFollowUps';
import type { SuggestedFollowUp } from '../../lib/api/client';

const suggestions: SuggestedFollowUp[] = [
  {
    id: 'one',
    category: 'compare',
    title: 'How do the selected views differ?',
    prompt: 'Compare the selected views and identify their distinct approaches.',
    basisCount: 2,
    evidence: 'SOURCE_ATTRIBUTED',
  },
  {
    id: 'two',
    category: 'review',
    title: 'How could these ideas be reviewed?',
    prompt: 'Summarize the common themes and distinguish them from differences.',
    basisCount: 1,
    evidence: 'AI_SYNTHESIS',
  },
];

describe('SuggestedFollowUps', () => {
  it('shows four skeleton cards while loading', () => {
    render(
      <SuggestedFollowUps
        suggestions={[]}
        status="loading"
        onAsk={jest.fn()}
        onRefresh={jest.fn()}
      />,
    );

    expect(screen.getByRole('status', { name: 'กำลังโหลดคำแนะนำ' })).toBeTruthy();
    expect(screen.getByTestId('suggestion-skeleton-grid').children).toHaveLength(4);
  });

  it('hides empty and error states', () => {
    const { rerender, container } = render(
      <SuggestedFollowUps
        suggestions={[]}
        status="success"
        onAsk={jest.fn()}
        onRefresh={jest.fn()}
      />,
    );
    expect(container.firstChild).toBeNull();

    rerender(
      <SuggestedFollowUps
        suggestions={suggestions}
        status="error"
        onAsk={jest.fn()}
        onRefresh={jest.fn()}
      />,
    );
    expect(container.firstChild).toBeNull();
  });

  it('toggles suggestions, shows evidence, clears selection, and submits selected prompts', () => {
    const onAsk = jest.fn();
    const onRefresh = jest.fn();
    render(
      <SuggestedFollowUps
        suggestions={suggestions}
        status="success"
        onAsk={onAsk}
        onRefresh={onRefresh}
      />,
    );

    const cards = screen.getAllByRole('button', { name: /How do|How could/ });
    expect(within(cards[0]).getByText('เปรียบเทียบ')).toBeTruthy();
    expect(within(cards[0]).getByText('อิงจาก 2 แหล่ง')).toBeTruthy();
    expect(within(cards[1]).getByText('AI-SYNTHESIS')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'ถามข้อที่เลือก (0)' }).hasAttribute('disabled')).toBe(true);

    fireEvent.click(cards[1]);
    fireEvent.click(cards[0]);
    expect(cards[0].getAttribute('aria-pressed')).toBe('true');
    expect(screen.getByRole('button', { name: 'ถามข้อที่เลือก (2)' }).hasAttribute('disabled')).toBe(false);
    fireEvent.click(screen.getByRole('button', { name: 'ถามข้อที่เลือก (2)' }));
    expect(onAsk).toHaveBeenCalledWith([
      suggestions[1].prompt,
      suggestions[0].prompt,
    ]);
    expect(cards[0].getAttribute('aria-pressed')).toBe('false');

    fireEvent.click(cards[0]);
    fireEvent.click(screen.getByRole('button', { name: 'ล้างตัวเลือก' }));
    expect(cards[0].getAttribute('aria-pressed')).toBe('false');
    fireEvent.click(screen.getByRole('button', { name: 'คำแนะนำชุดอื่น' }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});
