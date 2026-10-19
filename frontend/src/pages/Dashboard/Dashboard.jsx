import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, RotateCw } from 'lucide-react';
import { useDashboard } from '../../hooks/useDashboard';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { HeroBanner } from '../../components/dashboard/HeroBanner';
import { StatsGrid } from '../../components/dashboard/StatsGrid';
import { RecentActivity } from '../../components/dashboard/RecentActivity';
import { QuickActions } from '../../components/dashboard/QuickActions';

export function Dashboard({ onNotify }) {
  const navigate = useNavigate();
  const {
    summary,
    recentBroadcasts,
    buddy,
    loading,
    error,
    isTogglingBuddy,
    refetch,
    toggleBuddy,
  } = useDashboard();

  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refetch();
    setIsRefreshing(false);
    if (onNotify) {
      onNotify('Dashboard data refreshed');
    }
  };

  const handleToggleBuddy = () => {
    toggleBuddy((nextState) => {
      if (onNotify) {
        onNotify(`Buddy turned ${nextState ? 'ON' : 'OFF'}`);
      }
    });
  };

  return (
    <>
      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <div className="welcome-row">
        <div>
          <div className="eyebrow">
            <span className="eyebrow-line" aria-hidden="true" />
            CAMPUS ADMIN CONSOLE
          </div>
          <h1>Good evening, Admin</h1>
          <p className="subheading">Here’s what’s happening across your campus today.</p>
        </div>
        <button
          type="button"
          className="primary-button"
          onClick={() => navigate('/broadcast')}
        >
          <Plus size={17} aria-hidden="true" /> New broadcast
        </button>
      </div>

      <StatsGrid
        summary={summary}
        buddy={buddy}
        onToggleBuddy={handleToggleBuddy}
        isTogglingBuddy={isTogglingBuddy}
      />

      <div className="section-heading">
        <div>
          <h2>At a glance</h2>
          <p>Real-time overview of broadcasts and system operations</p>
        </div>
        <button
          type="button"
          className="text-button"
          onClick={handleRefresh}
          disabled={loading || isRefreshing}
        >
          <RotateCw
            size={14}
            className={loading || isRefreshing ? 'spin-icon' : ''}
            style={{
              animation: loading || isRefreshing ? 'spin 1s linear infinite' : 'none',
            }}
            aria-hidden="true"
          />
          {loading || isRefreshing ? 'Refreshing...' : 'Refresh data'}
        </button>
      </div>

      <div className="bottom-grid" style={{ marginBottom: '22px' }}>
        <RecentActivity broadcasts={recentBroadcasts} />
        <QuickActions />
      </div>

      <HeroBanner upcomingCount={summary.upcoming_count} />

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
}
