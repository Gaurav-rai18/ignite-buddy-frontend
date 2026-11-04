import React, { useState } from 'react';
import { CalendarClock, Grid3X3, FileSpreadsheet, ListOrdered, CalendarCheck, Link2 } from 'lucide-react';
import { PageIntro } from '../../components/ui/PageIntro';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { ScheduleForm } from '../../components/schedule/ScheduleForm';
import { ScheduleList } from '../../components/schedule/ScheduleList';
import { useSchedules } from '../../hooks/useSchedules';

export function Schedule({ onNotify }) {
  const {
    schedules,
    loading,
    configLoading,
    config,
    isSubmitting,
    error,
    formErrors,
    form,
    updateFormField,
    resetForm,
    submitSchedule,
    deleteSchedule,
    refetch,
    addBatch,
    removeBatch,
    addSubBatch,
    removeSubBatch,
    addTimeSlot,
    editTimeSlot,
    removeTimeSlot,
  } = useSchedules();

  const [activeTab, setActiveTab] = useState(
    form.excel_file || form.schedule_type === 'excel'
      ? 'excel'
      : form.onedrive_url
      ? 'link'
      : 'grid'
  );

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
  const excelSchedules = schedules.filter((s) => s.schedule_type === 'excel' || Boolean(s.excel_file || s.file_name)).length;
  const gridSchedules = schedules.filter((s) => Boolean(s.content_data) && s.schedule_type !== 'excel' && !s.excel_file).length;
  const otherSchedules = totalSchedules - excelSchedules - gridSchedules;

  return (
    <div className="schedule-page-container">
      {/* Intro Header */}
      <div className="schedule-header-row">
        <PageIntro
          eyebrow="ACADEMIC PLANNING & TIMETABLES"
          title="Schedule Planner"
          subtitle="Build dynamic 7-location lab timetable grids, manage batches & time slots, or upload Excel spreadsheets."
        />

        {/* Quick Header Stats */}
        <div className="schedule-header-stats">
          <div className="header-stat-pill" title="Total active scheduled items">
            <CalendarCheck size={14} className="text-primary" aria-hidden="true" />
            <span>
              <b>{totalSchedules}</b> scheduled
            </span>
          </div>

          <div className="header-stat-pill" title="Native interactive timetables">
            <Grid3X3 size={14} color="#014BAA" aria-hidden="true" />
            <span>
              <b>{gridSchedules}</b> {gridSchedules === 1 ? 'timetable' : 'timetables'}
            </span>
          </div>

          <div className="header-stat-pill" title="Excel spreadsheet timetables">
            <FileSpreadsheet size={14} color="#059669" aria-hidden="true" />
            <span>
              <b>{excelSchedules}</b> {excelSchedules === 1 ? 'Excel sheet' : 'Excel sheets'}
            </span>
          </div>

          {otherSchedules > 0 && (
            <div className="header-stat-pill" title="External link resources">
              <Link2 size={14} color="#0284C7" aria-hidden="true" />
              <span>
                <b>{otherSchedules}</b> {otherSchedules === 1 ? 'link' : 'links'}
              </span>
            </div>
          )}
        </div>
      </div>

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      {/* Main Layout Container */}
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
          config={config}
          onAddBatch={addBatch}
          onRemoveBatch={removeBatch}
          onAddSubBatch={addSubBatch}
          onRemoveSubBatch={removeSubBatch}
          onAddTimeSlot={addTimeSlot}
          onEditTimeSlot={editTimeSlot}
          onRemoveTimeSlot={removeTimeSlot}
        />

        <ScheduleList
          schedules={schedules}
          loading={loading}
          onCreateClick={handleFocusTitle}
          onDeleteSchedule={handleDeleteSchedule}
          config={config}
        />
      </div>
    </div>
  );
}
