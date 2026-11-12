import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

describe('Assignment Feature Integration Tests', () => {
  it('useAssignments.js imports and uses isRequestCancellation from utils/error', () => {
    const hookPath = resolve('src/hooks/useAssignments.js');
    const content = readFileSync(hookPath, 'utf8');

    assert.match(
      content,
      /import\s*\{\s*isRequestCancellation,\s*formatErrorMessage\s*\}\s*from\s*['"]\.\.\/utils\/error['"]/,
      'useAssignments.js must import isRequestCancellation from ../utils/error'
    );
    assert.match(
      content,
      /!isRequestCancellation\(err\)/,
      'useAssignments.js must guard setError with !isRequestCancellation(err)'
    );
  });

  it('App.jsx registers /assignments route inside AppLayout', () => {
    const appPath = resolve('src/app/App.jsx');
    const content = readFileSync(appPath, 'utf8');

    assert.match(
      content,
      /import\s*\{\s*Assignments\s*\}\s*from\s*['"]\.\.\/pages\/Assignments\/Assignments['"]/,
      'App.jsx must import Assignments page'
    );
    assert.match(
      content,
      /<Route\s+path="assignments"\s+element=\{<Assignments\s+onNotify=\{notify\}\s*\/>\}\s*\/>/,
      'App.jsx must declare /assignments route'
    );
  });

  it('AppLayout.jsx includes page title for /assignments', () => {
    const layoutPath = resolve('src/components/layout/AppLayout.jsx');
    const content = readFileSync(layoutPath, 'utf8');

    assert.match(
      content,
      /case\s+['"]\/assignments['"]:\s*return\s+['"]Assignments['"]/,
      'AppLayout.jsx must return Assignments title for /assignments'
    );
  });

  it('Sidebar.jsx includes /assignments in NAV_ITEMS with BookOpen icon', () => {
    const sidebarPath = resolve('src/components/layout/Sidebar.jsx');
    const content = readFileSync(sidebarPath, 'utf8');

    assert.match(
      content,
      /BookOpen/,
      'Sidebar.jsx must import BookOpen icon'
    );
    assert.match(
      content,
      /path:\s*['"]\/assignments['"],\s*name:\s*['"]Assignments['"],\s*icon:\s*BookOpen/,
      'Sidebar.jsx NAV_ITEMS must include /assignments entry'
    );
  });

  it('RolesPermissions.jsx includes assignments module definition', () => {
    const rolesPath = resolve('src/pages/RolesPermissions/RolesPermissions.jsx');
    const content = readFileSync(rolesPath, 'utf8');

    assert.match(
      content,
      /key:\s*['"]assignments['"]/,
      'RolesPermissions.jsx MODULES must include assignments key'
    );
  });

  it('assignmentService.js implements standard REST methods for assignments', () => {
    const servicePath = resolve('src/services/assignmentService.js');
    const content = readFileSync(servicePath, 'utf8');

    assert.match(content, /getAssignments:/, 'assignmentService must implement getAssignments');
    assert.match(content, /createAssignment:/, 'assignmentService must implement createAssignment');
    assert.match(content, /updateAssignmentDeadline:/, 'assignmentService must implement updateAssignmentDeadline');
    assert.match(content, /deleteAssignment:/, 'assignmentService must implement deleteAssignment');
  });

  it('Profile.jsx and Settings.jsx do not display Zero Trust Enforced text', () => {
    const profilePath = resolve('src/pages/Profile/Profile.jsx');
    const profileContent = readFileSync(profilePath, 'utf8');
    assert.doesNotMatch(
      profileContent,
      /Zero Trust Security Policy/,
      'Profile.jsx must not display Zero Trust Security Policy'
    );
    assert.doesNotMatch(
      profileContent,
      /<span className="activity-pill safe">ENFORCED<\/span>/,
      'Profile.jsx must not display ENFORCED pill'
    );

    const settingsPath = resolve('src/pages/Settings/Settings.jsx');
    const settingsContent = readFileSync(settingsPath, 'utf8');
    assert.doesNotMatch(
      settingsContent,
      /Zero Trust Standard/,
      'Settings.jsx must not display Zero Trust Standard'
    );
  });
});
