import React from 'react';
import { PageIntro } from '../../components/ui/PageIntro';
import { TimetableGridEditor } from '../../components/schedule/TimetableGridEditor';

export function Schedule({ onNotify }) {
  return (
    <>
      <PageIntro
        eyebrow="IGNITE PLANNING & SCHEDULING"
        title="Schedule & Timetable Management"
        subtitle="Create, edit, and publish weekly batch lecture schedules with deterministic room and lab allocations."
      />

      <TimetableGridEditor onNotify={onNotify} />
    </>
  );
}
