import React, { useState, useEffect } from 'react';
import {
  Bot,
  Info,
  ShieldAlert,
  Cpu,
  Mic,
  Eye,
  Sliders,
  BookOpen,
  AlertOctagon,
  Save,
  Check,
  Clock,
  CheckCircle2,
} from 'lucide-react';

export function BuddyDetails({
  settings,
  isUpdating,
  onToggleBuddy,
  onUpdateSetting,
  onSaveBatch,
  onNotify,
}) {
  const [form, setForm] = useState(settings);
  const [hasPromptChanged, setHasPromptChanged] = useState(false);
  const [hasKeywordsChanged, setHasKeywordsChanged] = useState(false);
  const [hasTestBuffersChanged, setHasTestBuffersChanged] = useState(false);

  useEffect(() => {
    setForm(settings);
  }, [settings]);

  const handleToggle = (key) => {
    const nextVal = !form[key];
    setForm((prev) => ({ ...prev, [key]: nextVal }));
    onUpdateSetting(key, nextVal, () => {
      onNotify?.(`${key.replace(/_/g, ' ')} updated`);
    });
  };

  const handleSavePrompt = () => {
    onUpdateSetting('llm_system_prompt', form.llm_system_prompt, () => {
      setHasPromptChanged(false);
      onNotify?.('Campus system directive saved successfully');
    });
  };

  const handleSaveKeywords = () => {
    onUpdateSetting('blocked_keywords', form.blocked_keywords, () => {
      setHasKeywordsChanged(false);
      onNotify?.('Safety blocked keywords updated');
    });
  };

  const handleSaveExamReason = () => {
    onUpdateSetting('exam_reason', form.exam_reason, () => {
      onNotify?.('Exam blackout notice updated');
    });
  };

  const handleSaveTestBuffers = () => {
    onUpdateSetting('test_buffer_before_minutes', parseInt(form.test_buffer_before_minutes, 10) || 15, () => {
      onUpdateSetting('test_buffer_after_minutes', parseInt(form.test_buffer_after_minutes, 10) || 15, () => {
        setHasTestBuffersChanged(false);
        onNotify?.('Test lockout buffer timings saved');
      });
    });
  };

  return (
    <div className="buddy-controls-grid">
      {/* 1. MASTER AVAILABILITY & EXAM LOCKDOWN */}
      <section className="panel control-info">
        <div className="panel-heading">
          <div>
            <h3>Master Availability & Exam Lockdown</h3>
            <p>Control overall campus availability and assessment restriction modes</p>
          </div>
          <div className="stat-icon primary" aria-hidden="true">
            <Bot size={18} />
          </div>
        </div>

        <div className="setting-row">
          <div>
            <b>Buddy Assistant Service</b>
            <small>Master ON/OFF switch across the campus</small>
          </div>
          <button
            type="button"
            className={`switch ${form.enabled ? 'switch-on' : ''}`}
            role="switch"
            aria-checked={form.enabled}
            aria-label="Toggle Buddy availability"
            disabled={isUpdating}
            onClick={onToggleBuddy}
          >
            <span />
          </button>
        </div>

        <div className="setting-row">
          <div>
            <b>Exam Assessment Mode</b>
            <small>Strict lockdown during lab tests and PRA evaluations</small>
          </div>
          <button
            type="button"
            className={`switch ${form.exam_mode ? 'switch-on' : ''}`}
            role="switch"
            aria-checked={form.exam_mode}
            aria-label="Toggle Exam mode"
            disabled={isUpdating}
            onClick={() => handleToggle('exam_mode')}
          >
            <span />
          </button>
        </div>

        {form.exam_mode && (
          <div className="exam-mode-banner" role="alert">
            <div className="exam-banner-header">
              <ShieldAlert size={16} />
              <strong>Exam Mode is Currently Active</strong>
            </div>
            <p>Trainee desktop assistants are restricted from providing assessment solutions.</p>
            <div className="exam-reason-field">
              <label htmlFor="exam-reason-input">Blackout reason shown to students:</label>
              <div className="input-with-button">
                <input
                  id="exam-reason-input"
                  type="text"
                  value={form.exam_reason || ''}
                  onChange={(e) => setForm({ ...form, exam_reason: e.target.value })}
                  placeholder="e.g. Assessment in progress. Buddy assistant is temporarily paused."
                  className="text-input"
                />
                <button
                  type="button"
                  className="secondary-button"
                  onClick={handleSaveExamReason}
                  disabled={isUpdating}
                >
                  <Save size={14} />
                  <span>Update</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* AUTOMATED TEST LOCKDOWN (SCHEDULE-DRIVEN) */}
      <section className="panel control-info">
        <div className="panel-heading">
          <div>
            <h3>Automated Test Lockdown (Schedule-Driven)</h3>
            <p>Automatically disable the Buddy during scheduled batch evaluations and tests</p>
          </div>
          <div className="stat-icon warning" aria-hidden="true" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' }}>
            <Clock size={18} />
          </div>
        </div>

        <div className="setting-row">
          <div>
            <b>Auto-Lock During Scheduled Tests</b>
            <small>Detects assessment lectures in the published timetable and disables Buddy automatically</small>
          </div>
          <button
            type="button"
            className={`switch ${form.test_auto_lock_enabled !== false ? 'switch-on' : ''}`}
            role="switch"
            aria-checked={form.test_auto_lock_enabled !== false}
            aria-label="Toggle auto test lock"
            disabled={isUpdating}
            onClick={() => handleToggle('test_auto_lock_enabled')}
          >
            <span />
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '12px', alignItems: 'flex-end', marginTop: '16px' }}>
          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              Buffer Before Test (minutes)
            </label>
            <input
              type="number"
              min="0"
              max="60"
              value={form.test_buffer_before_minutes ?? 15}
              onChange={(e) => {
                setForm({ ...form, test_buffer_before_minutes: e.target.value });
                setHasTestBuffersChanged(true);
              }}
              className="text-input"
              style={{ width: '100%', height: '36px' }}
            />
            <small style={{ fontSize: '11px', color: 'var(--text-secondary, #94a3b8)' }}>
              Locks buddy X mins before test starts
            </small>
          </div>

          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              Buffer After Test (minutes)
            </label>
            <input
              type="number"
              min="0"
              max="60"
              value={form.test_buffer_after_minutes ?? 15}
              onChange={(e) => {
                setForm({ ...form, test_buffer_after_minutes: e.target.value });
                setHasTestBuffersChanged(true);
              }}
              className="text-input"
              style={{ width: '100%', height: '36px' }}
            />
            <small style={{ fontSize: '11px', color: 'var(--text-secondary, #94a3b8)' }}>
              Keeps buddy locked X mins after test ends
            </small>
          </div>

          <button
            type="button"
            className="secondary-button"
            style={{ height: '36px', marginBottom: '18px' }}
            onClick={handleSaveTestBuffers}
            disabled={!hasTestBuffersChanged || isUpdating}
          >
            <Save size={14} />
            <span>Save Buffers</span>
          </button>
        </div>

        {/* Live Active Test Lock Status */}
        {form.active_test_lock?.is_locked ? (
          <div
            style={{
              marginTop: '16px',
              padding: '12px 16px',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              borderRadius: '8px',
            }}
            role="alert"
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ef4444', fontWeight: 600 }}>
              <ShieldAlert size={16} />
              <span>Automated Test Lockdown is Active</span>
            </div>
            <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#f87171' }}>
              {form.active_test_lock.reason}
            </p>
            <div style={{ fontSize: '12px', marginTop: '6px', color: '#94a3b8' }}>
              Target: <b>{form.active_test_lock.target_sub_batch}</b> · Venue: <b>{form.active_test_lock.location}</b> · Lockout Window: <b>{form.active_test_lock.lock_start} - {form.active_test_lock.lock_end}</b>
            </div>
          </div>
        ) : (
          <div
            style={{
              marginTop: '16px',
              padding: '10px 14px',
              background: 'rgba(34, 197, 94, 0.08)',
              border: '1px solid rgba(34, 197, 94, 0.2)',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '12.5px',
              color: '#4ade80',
            }}
          >
            <CheckCircle2 size={15} />
            <span>
              No active test lockdown right now. When a test is scheduled, Buddy will automatically lock {form.test_buffer_before_minutes ?? 15}m before and unlock {form.test_buffer_after_minutes ?? 15}m after.
            </span>
          </div>
        )}
      </section>

      {/* 2. AI MODEL & REASONING CONFIGURATION */}
      <section className="panel control-info">
        <div className="panel-heading">
          <div>
            <h3>AI Engine & Reasoning Parameters</h3>
            <p>Configure model selection, temperature, and campus behavioral directives</p>
          </div>
          <div className="stat-icon warning" aria-hidden="true">
            <Cpu size={18} />
          </div>
        </div>

        <div className="setting-row">
          <div>
            <b>Primary LLM Model</b>
            <small>Inference model used for trainee chat turns</small>
          </div>
          <select
            value={form.llm_model || 'llama3.2:3b'}
            onChange={(e) => {
              const val = e.target.value;
              setForm({ ...form, llm_model: val });
              onUpdateSetting('llm_model', val, () => onNotify?.(`Model switched to ${val}`));
            }}
            disabled={isUpdating}
            className="select-input"
            style={{ width: '180px' }}
          >
            <option value="llama3.2:3b">Llama 3.2 (3B Fast)</option>
            <option value="qwen2.5:3b">Qwen 2.5 (3B Code)</option>
            <option value="mistral:7b">Mistral (7B Instruct)</option>
            <option value="llama3.1:8b">Llama 3.1 (8B Large)</option>
          </select>
        </div>

        <div className="setting-row">
          <div>
            <b>Temperature (Creativity vs Determinism)</b>
            <small>0.0 = Deterministic/Academic, 1.0 = Highly Creative</small>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={form.llm_temperature ?? 0.3}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                setForm({ ...form, llm_temperature: val });
              }}
              onMouseUp={() => {
                onUpdateSetting('llm_temperature', form.llm_temperature, () => {
                  onNotify?.(`Temperature set to ${form.llm_temperature}`);
                });
              }}
              disabled={isUpdating}
              style={{ width: '120px', cursor: 'pointer' }}
            />
            <span style={{ fontSize: '12px', fontWeight: '700', minWidth: '32px' }}>
              {form.llm_temperature ?? 0.3}
            </span>
          </div>
        </div>

        <div className="prompt-config-field" style={{ marginTop: '14px' }}>
          <label htmlFor="system-prompt-textarea">
            <b>Campus System Directive / Behavior Persona:</b>
          </label>
          <textarea
            id="system-prompt-textarea"
            rows={3}
            value={form.llm_system_prompt || ''}
            onChange={(e) => {
              setForm({ ...form, llm_system_prompt: e.target.value });
              setHasPromptChanged(true);
            }}
            placeholder="e.g. Guide trainees with explanations and hints before giving complete code solutions."
            className="text-input textarea-input"
          />
          {hasPromptChanged && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '6px' }}>
              <button
                type="button"
                className="primary-button"
                onClick={handleSavePrompt}
                disabled={isUpdating}
              >
                <Save size={13} />
                <span>Save Persona Directive</span>
              </button>
            </div>
          )}
        </div>
      </section>

      {/* 3. HARDWARE & INPUT MODALITIES */}
      <section className="panel control-info">
        <div className="panel-heading">
          <div>
            <h3>Input Modalities & Desktop Sensors</h3>
            <p>Control trainee access to audio voice input, TTS feedback, and screen inspection</p>
          </div>
          <div className="stat-icon success" aria-hidden="true">
            <Mic size={18} />
          </div>
        </div>

        <div className="setting-row">
          <div>
            <b>Speech-to-Text (Voice Commands)</b>
            <small>Allow trainees to speak queries via local microphone</small>
          </div>
          <button
            type="button"
            className={`switch ${form.voice_enabled ? 'switch-on' : ''}`}
            role="switch"
            aria-checked={form.voice_enabled}
            disabled={isUpdating}
            onClick={() => handleToggle('voice_enabled')}
          >
            <span />
          </button>
        </div>

        <div className="setting-row">
          <div>
            <b>Text-to-Speech (Spoken Answers)</b>
            <small>Enable audio readback for trainee answers</small>
          </div>
          <button
            type="button"
            className={`switch ${form.voice_tts_enabled ? 'switch-on' : ''}`}
            role="switch"
            aria-checked={form.voice_tts_enabled}
            disabled={isUpdating}
            onClick={() => handleToggle('voice_tts_enabled')}
          >
            <span />
          </button>
        </div>

        <div className="setting-row">
          <div>
            <b>Screen Help & OCR Vision</b>
            <small>Allow Buddy to inspect error dialogs and stack traces on trainee screens</small>
          </div>
          <button
            type="button"
            className={`switch ${form.screen_help_enabled ? 'switch-on' : ''}`}
            role="switch"
            aria-checked={form.screen_help_enabled}
            disabled={isUpdating}
            onClick={() => handleToggle('screen_help_enabled')}
          >
            <span />
          </button>
        </div>

        <div className="setting-row">
          <div>
            <b>IDE Window & Context Tracking</b>
            <small>Track active code files in VS Code/IntelliJ for contextual answers</small>
          </div>
          <button
            type="button"
            className={`switch ${form.ide_tracking_enabled ? 'switch-on' : ''}`}
            role="switch"
            aria-checked={form.ide_tracking_enabled}
            disabled={isUpdating}
            onClick={() => handleToggle('ide_tracking_enabled')}
          >
            <span />
          </button>
        </div>
      </section>

      {/* 4. CAMPUS KNOWLEDGE BASE (RAG) SPACES */}
      <section className="panel control-info">
        <div className="panel-heading">
          <div>
            <h3>Campus Knowledge Base (RAG) Scopes</h3>
            <p>Determine which information repositories the assistant can search</p>
          </div>
          <div className="stat-icon primary" aria-hidden="true">
            <BookOpen size={18} />
          </div>
        </div>

        <div className="setting-row">
          <div>
            <b>Ignite Program Knowledge Space</b>
            <small>Search induction manuals, schedules, rules, and campus FAQs</small>
          </div>
          <button
            type="button"
            className={`switch ${form.rag_ignite_enabled ? 'switch-on' : ''}`}
            role="switch"
            aria-checked={form.rag_ignite_enabled}
            disabled={isUpdating}
            onClick={() => handleToggle('rag_ignite_enabled')}
          >
            <span />
          </button>
        </div>

        <div className="setting-row">
          <div>
            <b>General Technical Engineering Knowledge</b>
            <small>Search standard engineering reference guides and architecture docs</small>
          </div>
          <button
            type="button"
            className={`switch ${form.rag_general_enabled ? 'switch-on' : ''}`}
            role="switch"
            aria-checked={form.rag_general_enabled}
            disabled={isUpdating}
            onClick={() => handleToggle('rag_general_enabled')}
          >
            <span />
          </button>
        </div>

        <div className="setting-row">
          <div>
            <b>Personal Trainee Document Indexing</b>
            <small>Allow trainees to index their private lecture PDFs into local vector store</small>
          </div>
          <button
            type="button"
            className={`switch ${form.rag_personal_enabled ? 'switch-on' : ''}`}
            role="switch"
            aria-checked={form.rag_personal_enabled}
            disabled={isUpdating}
            onClick={() => handleToggle('rag_personal_enabled')}
          >
            <span />
          </button>
        </div>
      </section>

      {/* 5. SAFETY GUARDRAILS & RATE LIMITING */}
      <section className="panel control-info">
        <div className="panel-heading">
          <div>
            <h3>Safety Guardrails & Rate Limits</h3>
            <p>Prevent abuse, restrict sensitive keywords, and set hourly query quotas</p>
          </div>
          <div className="stat-icon warning" aria-hidden="true">
            <AlertOctagon size={18} />
          </div>
        </div>

        <div className="setting-row">
          <div>
            <b>Max Queries per Trainee / Hour</b>
            <small>Rate limit quota to preserve campus server resources</small>
          </div>
          <select
            value={form.max_queries_per_hour ?? 30}
            onChange={(e) => {
              const val = parseInt(e.target.value, 10);
              setForm({ ...form, max_queries_per_hour: val });
              onUpdateSetting('max_queries_per_hour', val, () => {
                onNotify?.(`Hourly query limit set to ${val === 0 ? 'Unlimited' : val}`);
              });
            }}
            disabled={isUpdating}
            className="select-input"
            style={{ width: '180px' }}
          >
            <option value="15">15 queries / hour</option>
            <option value="30">30 queries / hour (Standard)</option>
            <option value="60">60 queries / hour</option>
            <option value="0">Unlimited (No limit)</option>
          </select>
        </div>

        <div className="prompt-config-field" style={{ marginTop: '14px' }}>
          <label htmlFor="blocked-keywords-input">
            <b>Restricted / Prohibited Keywords (Comma-separated):</b>
          </label>
          <div className="input-with-button">
            <input
              id="blocked-keywords-input"
              type="text"
              value={form.blocked_keywords || ''}
              onChange={(e) => {
                setForm({ ...form, blocked_keywords: e.target.value });
                setHasKeywordsChanged(true);
              }}
              placeholder="e.g. exam leak, exam solutions, cheat, bypass policy"
              className="text-input"
            />
            {hasKeywordsChanged && (
              <button
                type="button"
                className="primary-button"
                onClick={handleSaveKeywords}
                disabled={isUpdating}
              >
                <Save size={13} />
                <span>Save</span>
              </button>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
