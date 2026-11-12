import React from 'react';
import { PageIntro } from '../../components/ui/PageIntro';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { AssignmentForm } from '../../components/assignment/AssignmentForm';
import { AssignmentList } from '../../components/assignment/AssignmentList';
import { useAssignments } from '../../hooks/useAssignments';

export function Assignments({ onNotify }) {
  const {
    assignments,
    loading,
    isSubmitting,
    error,
    formErrors,
    form,
    historyFilter,
    deadlineUpdating,
    setHistoryFilter,
    updateFormField,
    toggleRecipient,
    setRecipients,
    submitAssignment,
    updateDeadline,
    refetch,
  } = useAssignments();

  const handleSubmit = () => {
    submitAssignment((msg) => {
      if (onNotify) onNotify(msg);
    });
  };

  const handleFocusForm = () => {
    document.getElementById('assignment-topic')?.focus();
  };

  const handleUpdateDeadline = (id, deadline) => {
    updateDeadline(id, deadline, (msg) => {
      if (onNotify) onNotify(msg);
    });
  };

  return (
    <>
      <PageIntro
        eyebrow="ACADEMICS"
        title="Assignments"
        subtitle="Create and publish assignments for your students. Track and update deadlines from history."
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <div className="two-column">
        <AssignmentForm
          form={form}
          formErrors={formErrors}
          isSubmitting={isSubmitting}
          onChangeField={updateFormField}
          onToggleRecipient={toggleRecipient}
          onSetRecipients={setRecipients}
          onSubmit={handleSubmit}
        />
        <AssignmentList
          assignments={assignments}
          loading={loading}
          historyFilter={historyFilter}
          onFilterChange={setHistoryFilter}
          onCreateClick={handleFocusForm}
          deadlineUpdating={deadlineUpdating}
          onUpdateDeadline={handleUpdateDeadline}
        />
      </div>
    </>
  );
}
export default Assignments;
