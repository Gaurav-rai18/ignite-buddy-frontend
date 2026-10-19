import React from 'react';
import { useNavigate } from 'react-router-dom';
import { LayoutDashboard } from 'lucide-react';
import { EmptyState } from '../../components/ui/EmptyState';
import { PageIntro } from '../../components/ui/PageIntro';

export function NotFound() {
  const navigate = useNavigate();

  return (
    <>
      <PageIntro
        eyebrow="404 ERROR"
        title="Page not found"
        subtitle="The page you are looking for does not exist or has been moved."
      />
      <div className="panel" style={{ padding: '40px 20px', textAlign: 'center' }}>
        <EmptyState
          icon={LayoutDashboard}
          title="Looking for the dashboard?"
          text="Head back to the main control centre to manage announcements, schedules, and Buddy."
          action="Back to Dashboard"
          onClick={() => navigate('/dashboard')}
        />
      </div>
    </>
  );
}
