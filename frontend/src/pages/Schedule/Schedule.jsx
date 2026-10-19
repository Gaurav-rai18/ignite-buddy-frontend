import React from 'react';
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
    refetch,
  } = useSchedules();

  const handleSubmit = () => {
    submitSchedule((msg) => {
      if (onNotify) {
        onNotify(msg);
      }
    });
  };

  const handleFocusTitle = () => {
    document.getElementById('schedule-title')?.focus();
  };

  return (
    <>
      <PageIntro
        eyebrow="CONTENT PLANNING"
        title="Schedule a link"
        subtitle="Add a OneDrive link and choose when it should be published."
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <div className="two-column">
        <ScheduleForm
          form={form}
          formErrors={formErrors}
          isSubmitting={isSubmitting}
          onChangeField={updateFormField}
          onCancel={resetForm}
          onSubmit={handleSubmit}
        />
        <ScheduleList
          schedules={schedules}
          loading={loading}
          onCreateClick={handleFocusTitle}
        />
      </div>
    </>
  );
}
