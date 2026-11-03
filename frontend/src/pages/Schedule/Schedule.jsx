import React, { useState } from 'react';
import { CalendarClock, Grid3X3, Link2, ListOrdered, CalendarCheck } from 'lucide-react';
import { PageIntro } from '../../components/ui/PageIntro';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { ScheduleForm } from '../../components/schedule/ScheduleForm';
import { ScheduleList } from '../../components/schedule/ScheduleList';
import { useSchedules } from '../../hooks/useSchedules';

export function Schedule({ onNotify }) {
  const {
    schedules,
    loading,
    isSubmitting,
    error,
    formErrors,
    form,
    updateFormField,
    resetForm,
    submitSchedule,
    deleteSchedule,
    refetch,
  } = useSchedules();

  const [activeTab, setActiveTab] = useState(form.content_data ? 'grid' : 'link');

  const handleSubmit = () => {
    submitSchedule((msg) => {
      if (onNotify) {
        onNotify(msg);
      }
    });
  };

  const handleDeleteSchedule = async (id) => {
    if (!deleteSchedule) return false;
    return deleteSchedule(id, (msg) => {
      if (onNotify) {
        onNotify(msg);
      }
    });
  };

  const handleFocusTitle = () => {
    const el = document.getElementById('schedule-title');
    if (el) {
      el.focus();
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  // Quick stats
  const totalSchedules = schedules.length;
  const gridSchedules = schedules.filter((s) => Boolean(s.content_data)).length;
  const linkSchedules = totalSchedules - gridSchedules;

  return (
    <div className="schedule-page-container">
      {/* Intro Header */}
      <div className="schedule-header-row">
        <PageIntro
          eyebrow="ACADEMIC PLANNING & TIMETABLES"
          title="Schedule Planner"
          subtitle="Build native lab timetable grids or schedule OneDrive learning resources for students."
        />

        {/* Quick Header Stats */}
        <div className="schedule-header-stats">
          <div className="header-stat-pill" title="Total active scheduled items">
            <CalendarCheck size={14} className="text-primary" aria-hidden="true" />
            <span>
              <b>{totalSchedules}</b> scheduled
            </span>
          </div>

          <div className="header-stat-pill" title="Native timetables">
            <Grid3X3 size={14} color="#014BAA" aria-hidden="true" />
            <span>
              <b>{gridSchedules}</b> {gridSchedules === 1 ? 'timetable' : 'timetables'}
            </span>
          </div>

          <div className="header-stat-pill" title="OneDrive links">
            <Link2 size={14} color="#0284C7" aria-hidden="true" />
            <span>
              <b>{linkSchedules}</b> {linkSchedules === 1 ? 'link' : 'links'}
            </span>
          </div>
        </div>
      </div>

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      {/* Main Layout Container: adapts smoothly based on activeTab */}
      <div className={activeTab === 'grid' ? 'schedule-grid-layout' : 'two-column schedule-link-layout'}>
        <ScheduleForm
          form={form}
          formErrors={formErrors}
          isSubmitting={isSubmitting}
          onChangeField={updateFormField}
          onCancel={resetForm}
          onSubmit={handleSubmit}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />

        <ScheduleList
          schedules={schedules}
          loading={loading}
          onCreateClick={handleFocusTitle}
          onDeleteSchedule={handleDeleteSchedule}
        />
      </div>
    </div>
  );
}
