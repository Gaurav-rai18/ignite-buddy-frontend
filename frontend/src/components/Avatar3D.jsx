import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

/**
 * Standard animation synonym mappings.
 *
 * Different 3D model creators use different names for common character actions
 * (e.g. "walk", "walking", "run", "Walk_Fwd", "mixamo.com|Layer0").
 * This mapping categorizes synonyms so models with arbitrary naming conventions
 * can trigger the appropriate animation based on the assistant's state.
 */
export const ANIMATION_SYNONYMS = {
  idle: [
    "idle", "stand", "standing", "breath", "breathing", "neutral", "ambient",
    "default", "rest", "loop", "wait", "waiting", "pose"
  ],
  listening: [
    "listen", "listening", "hear", "hearing", "attention", "alert", "focus",
    "look", "look_around", "ear"
  ],
  thinking: [
    "think", "thinking", "ponder", "pondering", "wonder", "wondering", "inspect",
    "scratch", "head_scratch", "idea", "search"
  ],
  speaking: [
    "talk", "talking", "speak", "speaking", "speech", "chat", "chatting",
    "mouth", "say", "saying", "explain", "present"
  ],
  executing: [
    "walk", "walking", "run", "running", "action", "work", "working", "type",
    "typing", "move", "moving", "treadmill", "operate"
  ],
  alert: [
    "alert", "alarm", "surprise", "surprised", "shock", "warning", "wave",
    "cheer", "jump"
  ],
  success: [
    "wave", "waving", "cheer", "cheering", "happy", "nod", "nodding", "yes",
    "agree", "thumbs_up", "celebrate", "victory"
  ],
  offline: [
    "sleep", "sleeping", "sit", "sitting", "down", "off", "power_down",
    "deactivate", "die"
  ],
};

/**
 * Normalizes an animation clip name by stripping armature/mixamo prefixes
 * and converting separators to spaces.
 */
function normalizeName(name) {
  return String(name || "")
    .toLowerCase()
    .replace(/^(armature\||mixamo\.com\||root\||bip01\|)/, "")
    .replace(/[_\-./]+/g, " ")
    .trim();
}

/**
 * Resolves an animation clip from an array of GLTF animation clips for a target mood / action.
 *
 * Checks explicit custom mappings first, then searches against the synonym dictionary,
 * and falls back to idle or the first available clip.
 *
 * @param {THREE.AnimationClip[]} clips Available GLTF animation clips.
 * @param {string} mood Target action or mood ("idle", "listening", "thinking", "speaking", "executing", etc.).
 * @param {Record<string, string>} [customMap] Optional user-defined mapping (e.g. { walk: "Walk_01", idle: "Stand" }).
 * @returns {THREE.AnimationClip|null}
 */
export function resolveAnimationClip(clips, mood, customMap = {}) {
  if (!clips || !clips.length) return null;

  const target = (mood || "idle").toLowerCase();

  // 1. Check explicit custom mapping (e.g. customMap.walk or customMap.executing)
  const explicit = customMap[target] || (target === "executing" ? customMap["walk"] : null);
  if (explicit) {
    const explicitClean = normalizeName(explicit);
    const found = clips.find((c) => {
      const cClean = normalizeName(c.name);
      return cClean === explicitClean || cClean.includes(explicitClean) || explicitClean.includes(cClean);
    });
    if (found) return found;
  }

  // 2. Map mood aliases
  const canonicalMood = target === "hearing" ? "listening" : target;
  const synonyms = ANIMATION_SYNONYMS[canonicalMood] || [canonicalMood];

  // Search by token match or substring match
  for (const syn of synonyms) {
    const synLower = syn.toLowerCase();
    const found = clips.find((c) => {
      const cClean = normalizeName(c.name);
      const tokens = cClean.split(/\s+/);
      return tokens.includes(synLower) || cClean === synLower || cClean.includes(synLower);
    });
    if (found) return found;
  }

  // 3. Fallback to idle if requested mood was not found
  if (canonicalMood !== "idle") {
    const idleSynonyms = ANIMATION_SYNONYMS.idle;
    for (const syn of idleSynonyms) {
      const synLower = syn.toLowerCase();
      const found = clips.find((c) => {
        const cClean = normalizeName(c.name);
        const tokens = cClean.split(/\s+/);
        return tokens.includes(synLower) || cClean === synLower || cClean.includes(synLower);
      });
      if (found) return found;
    }
  }

  // 4. Default to first clip
  return clips[0];
}

const BLUE = 0x2f5bea;
const CYAN = 0x4dd2ff;

/**
 * Builds a procedural robot when no custom GLB model is supplied or when GLB fails to load.
 */
function buildRobot() {
  const g = new THREE.Group();
  const body = new THREE.MeshStandardMaterial({ color: BLUE, roughness: 0.35, metalness: 0.2 });
  const white = new THREE.MeshStandardMaterial({ color: 0xf4f6fb, roughness: 0.4 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x141a2b, roughness: 0.2, metalness: 0.4 });
  const glow = new THREE.MeshStandardMaterial({ color: CYAN, emissive: CYAN, emissiveIntensity: 1.4 });
  const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.45, 0.5, 8, 16), body);
  torso.position.y = -0.55;
  const head = new THREE.Group();
  head.position.y = 0.45;
  const skull = new THREE.Mesh(new THREE.SphereGeometry(0.62, 32, 24), white);
  const visor = new THREE.Mesh(new THREE.SphereGeometry(0.5, 32, 24), dark);
  visor.scale.set(1.05, 0.7, 0.55);
  visor.position.set(0, 0.02, 0.38);
  const eyeL = new THREE.Mesh(new THREE.SphereGeometry(0.075, 16, 12), glow);
  eyeL.position.set(-0.2, 0.1, 0.69);
  const eyeR = eyeL.clone();
  eyeR.position.x = 0.2;
  const mouth = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.05, 0.03), glow);
  mouth.position.set(0, -0.1, 0.7);
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.28, 8), white);
  stem.position.y = 0.76;
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.07, 16, 12), glow);
  bulb.position.y = 0.94;
  head.add(skull, visor, eyeL, eyeR, mouth, stem, bulb);
  const armL = new THREE.Mesh(new THREE.CapsuleGeometry(0.11, 0.4, 6, 10), white);
  armL.position.set(-0.62, -0.5, 0);
  armL.rotation.z = 0.25;
  const armR = armL.clone();
  armR.position.x = 0.62;
  armR.rotation.z = -0.25;
  const ring = new THREE.Mesh(new THREE.TorusGeometry(1.0, 0.025, 8, 64), glow);
  ring.rotation.x = Math.PI / 2;
  ring.position.y = -1.2;
  g.add(torso, head, armL, armR, ring);
  return { root: g, head, eyes: [eyeL, eyeR], mouth, bulb, ring, glow, arms: [armL, armR] };
}

/**
 * 3D character viewport.
 *
 * Renders custom GLB models or a procedural robot character on a transparent canvas.
 * Transitions between animations smoothly via Three.js AnimationMixer cross-fading
 * matching the assistant's real-time state.
 */
export default function Avatar3D({ mood, glb, onFail, animationMap = {} }) {
  const mount = useRef(null);
  const moodRef = useRef(mood);
  moodRef.current = mood;
  const animationMapRef = useRef(animationMap);
  animationMapRef.current = animationMap;

  useEffect(() => {
    const el = mount.current;
    let renderer;
    let raf = 0;
    let disposed = false;
    let mixer = null;
    let clips = [];
    let currentAction = null;
    let currentClipName = null;
    let lastMood = null;

    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "low-power" });
    } catch {
      onFail?.();
      return undefined;
    }

    renderer.setClearColor(0x000000, 0);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    const W = el.clientWidth || 200;
    const H = el.clientHeight || 230;
    renderer.setSize(W, H);
    el.appendChild(renderer.domElement);
    renderer.domElement.addEventListener("webglcontextlost", (e) => {
      e.preventDefault();
      onFail?.();
    });

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(32, W / H, 0.1, 50);
    camera.position.set(0, 0.05, 5.3);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x6677aa, 1.5));
    const key = new THREE.DirectionalLight(0xffffff, 2.2);
    key.position.set(2, 3, 4);
    scene.add(key);

    const pivot = new THREE.Group();
    scene.add(pivot);
    let robot = null;
    let model = null;

    const loader = new GLTFLoader();

    const applyModel = (gltf) => {
      if (disposed) return;
      model = gltf.scene;
      const box = new THREE.Box3().setFromObject(model);
      const size = box.getSize(new THREE.Vector3());
      const c = box.getCenter(new THREE.Vector3());
      const k = 2.6 / Math.max(size.y, 0.001);
      model.scale.setScalar(k);
      model.position.set(-c.x * k, -c.y * k, -c.z * k);
      pivot.add(model);

      if (gltf.animations?.length) {
        clips = gltf.animations;
        mixer = new THREE.AnimationMixer(model);
        const initialClip = resolveAnimationClip(clips, moodRef.current, animationMapRef.current);
        if (initialClip) {
          currentAction = mixer.clipAction(initialClip);
          currentAction.play();
          currentClipName = initialClip.name;
          lastMood = moodRef.current;
        }
      }
    };

    const fallbackToExisting3D = () => {
      if (disposed) return;
      // If a secondary glb is specified and not /model.glb, try it
      if (glb && glb !== "/model.glb") {
        loader.load(
          glb,
          (gltf) => {
            applyModel(gltf);
          },
          undefined,
          () => {
            if (!disposed) {
              robot = buildRobot();
              pivot.add(robot.root);
            }
          }
        );
      } else {
        // Fallback to existing 3D procedural character (never degrades to 2D)
        robot = buildRobot();
        pivot.add(robot.root);
      }
    };

    // Primary: Attempt to load custom /model.glb from frontend/public folder
    loader.load(
      "/model.glb",
      (gltf) => {
        applyModel(gltf);
      },
      undefined,
      () => {
        // Fallback to existing 3D model
        fallbackToExisting3D();
      }
    );

    let lastSec = performance.now() * 0.001;
    const startSec = lastSec;
    let lastFrame = 0;

    const loop = (now) => {
      raf = requestAnimationFrame(loop);
      if (document.hidden || now - lastFrame < 33) return; // ~30 fps cap for low power consumption
      lastFrame = now;
      const nowSec = performance.now() * 0.001;
      const delta = Math.min(Math.max(nowSec - lastSec, 0.001), 0.1);
      lastSec = nowSec;
      const t = nowSec - startSec;
      const m = moodRef.current;

      // Handle GLTF animation transitions on mood change
      if (mixer && clips.length && m !== lastMood) {
        lastMood = m;
        const nextClip = resolveAnimationClip(clips, m, animationMapRef.current);
        if (nextClip && nextClip.name !== currentClipName) {
          const nextAction = mixer.clipAction(nextClip);
          nextAction.reset();
          nextAction.enabled = true;
          nextAction.setEffectiveTimeScale(1);
          nextAction.setEffectiveWeight(1);
          if (currentAction) {
            currentAction.crossFadeTo(nextAction, 0.35, true);
          }
          nextAction.play();
          currentAction = nextAction;
          currentClipName = nextClip.name;
        }
      }

      // Procedural secondary motion
      const bob = m === "offline" ? 0 : Math.sin(t * 2) * 0.05;
      if (m === "alert") {
        pivot.position.y = bob + Math.abs(Math.sin(t * 8)) * 0.12;
        pivot.rotation.z = Math.sin(t * 12) * 0.12;
        pivot.rotation.y = Math.sin(t * 6) * 0.22;
      } else {
        pivot.position.y = bob;
        pivot.rotation.y = m === "thinking" ? t * 1.4 : Math.sin(t * 0.7) * 0.28;
        pivot.rotation.z = 0;
      }
      pivot.scale.setScalar(m === "hearing" ? 1 + Math.sin(t * 12) * 0.025 : 1);

      if (robot) {
        const listening = m === "listening" || m === "hearing";
        robot.ring.visible = listening;
        robot.ring.scale.setScalar(1 + Math.sin(t * (m === "hearing" ? 10 : 4)) * 0.08);
        robot.head.rotation.x = listening ? -0.12 : m === "speaking" ? Math.sin(t * 6) * 0.06 : 0;
        robot.mouth.scale.y = m === "speaking" ? 0.4 + Math.abs(Math.sin(t * 14)) * 2.6 : 1;
        robot.bulb.visible = m === "thinking" ? Math.sin(t * 10) > 0 : true;
        robot.glow.color.setHex(m === "offline" ? 0x777777 : m === "alert" ? 0xffb74d : CYAN);
        robot.glow.emissive.setHex(m === "offline" ? 0x222222 : m === "alert" ? 0xffb74d : CYAN);
        robot.arms[0].rotation.z = 0.25 + (m === "alert" ? Math.abs(Math.sin(t * 8)) * 1.2 : 0);
      }

      mixer?.update(delta);
      renderer.render(scene, camera);
    };

    raf = requestAnimationFrame(loop);

    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      scene.traverse((o) => {
        o.geometry?.dispose?.();
        const mat = o.material;
        (Array.isArray(mat) ? mat : [mat]).forEach((x) => x?.dispose?.());
      });
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, [glb, onFail]);

  return <div ref={mount} className="avatar3d" />;
}
