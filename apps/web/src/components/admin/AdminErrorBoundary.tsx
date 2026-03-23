import { Component, type ReactNode, type ErrorInfo } from 'react';

interface Props {
  children: ReactNode;
}
interface State {
  hasError: boolean;
  error: Error | null;
}

export class AdminErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[AdminErrorBoundary]', error, info.componentStack);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          data-testid="admin-error-boundary"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '80px 24px',
            gap: '16px',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '32px' }}>{'\u26A0'}</div>
          <div style={{ fontSize: '18px', fontWeight: 600 }}>Something went wrong</div>
          <div style={{ fontSize: '13px', opacity: 0.6, maxWidth: '400px' }}>
            {this.state.error?.message ?? 'An unexpected error occurred in the admin panel.'}
          </div>
          <button
            onClick={this.handleRetry}
            style={{
              padding: '8px 20px',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '13px',
              background: '#4b7dff',
              color: '#fff',
            }}
          >
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
