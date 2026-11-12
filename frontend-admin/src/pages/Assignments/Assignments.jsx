import React from 'react';
import { PageIntro } from '../../components/ui/PageIntro';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { AssignmentForm } from '../../components/assignment/AssignmentForm';
import { AssignmentList } from '../../components/assignment/AssignmentList';
import { AssignmentSubmissionsModal } from '../../components/assignment/AssignmentSubmissionsModal';
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
    publishingId,
    submissionsAssignmentId,
    submissions,
    submissionsLoading,
    evaluationSaving,
    setHistoryFilter,
    updateFormField,
    toggleRecipient,
    setRecipients,
    submitAssignment,
    publishAssignment,
    updateDeadline,
    openSubmissions,
    closeSubmissions,
    evaluateSubmission,
    refetch,
  } = useAssignments();

  const notify = (msg) => {
    if (onNotify) onNotify(msg);
  };

  const handleSubmit = (options) => {
    submitAssignment(notify, options);
  };

  const handleFocusForm = () => {
    document.getElementById('assignment-topic')?.focus();
  };

  const handleUpdateDeadline = (id, deadline) => {
    updateDeadline(id, deadline, notify);
  };

  const handlePublish = (id) => {
    publishAssignment(id, notify);
  };

  const activeAssignment = assignments.find(
    (a) => String(a.id) === String(submissionsAssignmentId)
  );

  const handleEvaluate = (recipientId, evaluationData) => {
    evaluateSubmission(recipientId, evaluationData, notify);
  };

  return (
    <>
      <PageIntro
        eyebrow="ACADEMICS"
        title="Assignments"
        subtitle="Create, publish and manage assignments for your students. Review submissions, evaluate work and share feedback."
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
          onPublish={handlePublish}
          publishingId={publishingId}
          onViewSubmissions={openSubmissions}
        />
      </div>

      <AssignmentSubmissionsModal
        isOpen={submissionsAssignmentId !== null}
        assignment={activeAssignment}
        submissions={submissions}
        loading={submissionsLoading}
        evaluationSaving={evaluationSaving}
        onClose={closeSubmissions}
        onEvaluate={handleEvaluate}
      />
    </>
  );
}
export default Assignments;
