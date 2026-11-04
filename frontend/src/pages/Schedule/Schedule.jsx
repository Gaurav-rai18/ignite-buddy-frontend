/**
 * Schedule.jsx — Top-Level Schedule Management Page.
 *
 * Features:
 *  - Integrates `useSchedules()` hook to manage all timetable CRUD operations,
 *    dynamic locations, batch configuration, and Excel upload workflows.
 *  - Provides page intro banner and error messaging.
 *  - Renders full-width `ScheduleForm` for creating and publishing academic timetables.
 */

import React, { useState } from 'react';
import { PageIntro } from '../../components/ui/PageIntro';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { ScheduleForm } from '../../components/schedule/ScheduleForm';
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

  return (
    <div className="schedule-page-container">
      {/* Intro Header */}
      <div className="schedule-header-row">
        <PageIntro
          eyebrow="ACADEMIC PLANNING & TIMETABLES"
          title="Schedule Planner"
          subtitle="Build dynamic 7-location lab timetable grids, manage batches & time slots, or upload Excel spreadsheets."
        />
      </div>

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      {/* Main Full-Width Schedule Creation Area */}
      <div className="schedule-full-layout">
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
      </div>
    </div>
  );
}
