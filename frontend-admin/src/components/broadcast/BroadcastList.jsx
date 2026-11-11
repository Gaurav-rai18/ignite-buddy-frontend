import React, { useState, useMemo } from 'react';
import { Megaphone, Users, Send, Search, Clock, CheckCircle } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';
import { formatDate } from '../../utils/date';

export function BroadcastList({ broadcasts = [], loading = false, onCreateClick }) {
  const [searchQuery, setSearchQuery] = useState('');

  const formatAudience = (item) => {
    if (item.recipient_type === 'COHORT') return `Cohort: ${item.target_cohort_code || 'Targeted'}`;
    if (item.recipient_type === 'BATCH') return `Batch: ${item.target_batch_code || 'Targeted'}`;
    if (item.recipient_type === 'SUB_BATCH') return `Sub-Batch: ${item.target_sub_batch_code || 'Targeted'}`;
    if (item.recipient_type === 'ROLE') return `Role: ${item.target_role || 'Targeted'}`;
    if (item.recipient_type === 'USERS' || item.recipient_type === 'USER') return `Specific: ${item.target_username || 'Selected users'}`;
    return item.audience || 'All users';
  };

  const filteredBroadcasts = useMemo(() => {
    if (!searchQuery.trim()) return broadcasts;
    const q = searchQuery.toLowerCase();
    return broadcasts.filter((item) => {
      const title = (item.title || '').toLowerCase();
      const message = (item.message || '').toLowerCase();
      const audience = formatAudience(item).toLowerCase();
      return title.includes(q) || message.includes(q) || audience.includes(q);
    });
  }, [broadcasts, searchQuery]);

  return (
    <section className="panel list-panel">
      <div className="panel-heading" style={{ marginBottom: '14px' }}>
        <div>
          <h3>Announcement History</h3>
          <p>{broadcasts.length} total broadcast announcements</p>
        </div>
        <span className="count-badge" aria-label={`${broadcasts.length} announcements`}>
          {broadcasts.length}
        </span>
      </div>

      {broadcasts.length > 0 && (
        <div style={{ marginBottom: '14px' }}>
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <Search
              size={14}
              style={{ position: 'absolute', left: '10px', color: 'var(--color-text-secondary)', pointerEvents: 'none' }}
              aria-hidden="true"
            />
            <input
              type="text"
              placeholder="Search announcements by title or content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="text-input"
              style={{
                width: '100%',
                paddingLeft: '32px',
                fontSize: '12px',
                borderRadius: '8px',
                paddingTop: '7px',
                paddingBottom: '7px',
              }}
            />
          </div>
        </div>
      )}

      {loading && broadcasts.length === 0 ? (
        <div style={{ padding: '36px', textAlign: 'center', color: 'var(--color-text-secondary)', fontSize: '12px' }}>
          Loading announcements...
        </div>
      ) : broadcasts.length > 0 ? (
        <div className="broadcast-history-scroll">
          {filteredBroadcasts.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-secondary)', fontSize: '12px' }}>
              No announcements match "{searchQuery}".
            </div>
          ) : (
            filteredBroadcasts.map((item) => (
              <article
                className="list-entry broadcast-entry-card"
                key={item.id}
                style={{
                  padding: '12px 14px',
                  borderRadius: '8px',
                  border: '1px solid var(--color-border-light)',
                  background: '#FAFAFC',
                  marginBottom: '8px',
                }}
              >
                <div className="entry-top" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="entry-icon" aria-hidden="true" style={{ width: '26px', height: '26px', borderRadius: '6px' }}>
                      <Megaphone size={13} />
                    </span>
                    <h4 style={{ margin: 0, fontSize: '13px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                      {item.title}
                    </h4>
                  </div>
                  <span
                    className="published-tag"
                    style={{
                      fontSize: '10px',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '12px',
                      background: '#DCFCE7',
                      color: '#15803D',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <CheckCircle size={10} /> Sent
                  </span>
                </div>

                <p style={{ margin: '6px 0 10px 0', fontSize: '11.5px', color: 'var(--color-text-secondary)', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
                  {item.message}
                </p>

                <div
                  className="entry-meta"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '10.5px',
                    color: 'var(--color-text-secondary)',
                    paddingTop: '6px',
                    borderTop: '1px solid rgba(0, 0, 0, 0.05)',
                  }}
                >
                  <span style={{ fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '5px', color: '#4338CA' }}>
                    <Users size={12} aria-hidden="true" />
                    {formatAudience(item)}
                  </span>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={11} aria-hidden="true" />
                    {formatDate(item.created_at)}
                  </span>
                </div>
              </article>
            ))
          )}
        </div>
      ) : (
        <EmptyState
          icon={Send}
          title="No announcements yet"
          text="Your published announcements will appear here."
          action={onCreateClick ? 'Create announcement' : undefined}
          onClick={onCreateClick}
        />
      )}
    </section>
  );
}
