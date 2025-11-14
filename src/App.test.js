import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';

describe('App', () => {
  afterEach(() => {
    jest.restoreAllMocks();
    delete global.fetch;
  });

  test('renders hero heading', () => {
    render(<App />);
    expect(screen.getByText(/Empowering ethical AI builders on campus/i)).toBeInTheDocument();
  });

  test('logs message from backend when hello button clicked', async () => {
    const fetchMock = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ message: 'Hello world' }),
      }),
    );
    global.fetch = fetchMock;
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation(() => {});

    render(<App />);
    fireEvent.click(screen.getByRole('button', { name: /say hello/i }));

    await waitFor(() => expect(consoleSpy).toHaveBeenCalledWith('Backend says:', 'Hello world'));
    expect(fetchMock).toHaveBeenCalledWith('/api/hello');
  });
});
