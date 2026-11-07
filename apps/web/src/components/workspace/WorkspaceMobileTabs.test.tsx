import { fireEvent, render, screen } from '@testing-library/react';
import { WorkspaceMobileTabs } from './WorkspaceMobileTabs';

describe('WorkspaceMobileTabs', () => {
  it.each([
    ['reader', 'อ่าน'],
    ['sources', 'Sources'],
    ['dialogue', 'ตัฟซีร'],
    ['studio', 'Studio'],
  ] as const)('selects the %s tab', (view, label) => {
    const onSelect = jest.fn();
    const result = render(<WorkspaceMobileTabs activeView="reader" onSelect={onSelect} />);

    fireEvent.click(screen.getByRole('button', { name: label }));

    expect(onSelect).toHaveBeenCalledWith(view);
    result.rerender(<WorkspaceMobileTabs activeView={view} onSelect={onSelect} />);
    expect(screen.getByRole('button', { name: label }).getAttribute('aria-current')).toBe('page');
    expect(screen.getByRole('button', { name: label }).className).toContain('bg-[#E6F4F1]');
  });

  it('keeps the existing labels and active/inactive presentation', () => {
    render(<WorkspaceMobileTabs activeView="dialogue" onSelect={jest.fn()} />);

    expect(screen.getByRole('button', { name: 'อ่าน' }).className).toContain('text-slate-500');
    expect(screen.getByRole('button', { name: 'ตัฟซีร' }).className).toContain('text-[#0E5E4F]');
    expect(screen.getAllByRole('button')).toHaveLength(4);
  });
});
