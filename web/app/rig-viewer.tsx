import { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { asset } from '@/lib/asset';
import { Switch } from '@/components/ui/switch';
export default function RigViewer() {
  const host = useRef<HTMLDivElement>(null),
    play = useRef(true),
    show = useRef(false);
  const [playing, setPlaying] = useState(true),
    [skeleton, setSkeleton] = useState(false),
    [status, setStatus] = useState('正在加载三维角色…');
  useEffect(() => {
    let cleanup = () => {};
    let stopped = false;
    (async () => {
      const T = await import('three');
      const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
      const { OrbitControls } =
        await import('three/addons/controls/OrbitControls.js');
      if (stopped || !host.current) return;
      const el = host.current,
        scene = new T.Scene();
      scene.background = new T.Color('#151d22');
      const camera = new T.PerspectiveCamera(35, 1, 0.01, 100);
      camera.position.set(2, 1.55, 4.5);
      const renderer = new T.WebGLRenderer({ antialias: true });
      renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
      renderer.toneMapping = T.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.45;
      el.appendChild(renderer.domElement);
      const controls = new OrbitControls(camera, renderer.domElement);
      controls.target.set(0, 0.95, 0);
      controls.enableDamping = true;
      controls.maxDistance = 9;
      controls.minDistance = 1.2;
      controls.maxPolarAngle = Math.PI * 0.53;
      scene.add(new T.HemisphereLight(0xe2efff, 0x566773, 3));
      const key = new T.DirectionalLight(0xffecdc, 4);
      key.position.set(3, 5, 4);
      scene.add(key);
      const rim = new T.DirectionalLight(0xa4e0ef, 3);
      rim.position.set(-3, 3, -2);
      scene.add(rim);
      scene.add(new T.GridHelper(8, 40, 0x526269, 0x2b363d));
      let mixer: InstanceType<typeof T.AnimationMixer> | undefined,
        helper: InstanceType<typeof T.SkeletonHelper> | undefined;
      const materials: InstanceType<typeof T.Material>[] = [];
      new GLTFLoader().load(
        asset('/media/character.glb'),
        (g) => {
          if (stopped) return;
          scene.add(g.scene);
          helper = new T.SkeletonHelper(g.scene);
          (
            helper.material as InstanceType<typeof T.LineBasicMaterial>
          ).depthTest = false;
          helper.renderOrder = 10;
          scene.add(helper);
          g.scene.traverse((o) => {
            const m = o as InstanceType<typeof T.Mesh>;
            if (m.isMesh)
              materials.push(
                ...(Array.isArray(m.material) ? m.material : [m.material]),
              );
          });
          if (g.animations.length) {
            mixer = new T.AnimationMixer(g.scene);
            mixer.clipAction(g.animations[0]).play();
          }
          setStatus('');
        },
        undefined,
        () => setStatus('模型加载失败，请刷新重试。'),
      );
      const resize = () => {
        renderer.setSize(el.clientWidth, el.clientHeight);
        camera.aspect = el.clientWidth / el.clientHeight;
        camera.updateProjectionMatrix();
      };
      const observer = new ResizeObserver(resize);
      observer.observe(el);
      resize();
      let previous = performance.now();
      let id = 0;
      const tick = () => {
        id = requestAnimationFrame(tick);
        const now = performance.now();
        const dt = Math.min((now - previous) / 1000, 0.1);
        previous = now;
        if (play.current) mixer?.update(dt);
        if (helper) helper.visible = show.current;
        for (const m of materials) {
          m.transparent = show.current;
          m.opacity = show.current ? 0.28 : 1;
          m.depthWrite = !show.current;
        }
        controls.update();
        renderer.render(scene, camera);
      };
      tick();
      cleanup = () => {
        cancelAnimationFrame(id);
        observer.disconnect();
        controls.dispose();
        scene.traverse((o) => {
          const m = o as InstanceType<typeof T.Mesh>;
          m.geometry?.dispose();
          if (m.material)
            for (const mat of Array.isArray(m.material)
              ? m.material
              : [m.material])
              mat.dispose();
        });
        renderer.dispose();
        renderer.domElement.remove();
      };
    })().catch(() =>
      setStatus('此设备暂时无法启动三维视图。可下载 GLB 在 Blender 中打开。'),
    );
    return () => {
      stopped = true;
      cleanup();
    };
  }, []);
  return (
    <div className="rig-stage">
      <div
        ref={host}
        className="three-host"
        aria-label="可旋转的角色骨架动画"
      />
      {status && <output className="viewer-status">{status}</output>}
      <div className="rig-controls">
        <Button
          variant="secondary"
          onClick={() => {
            play.current = !playing;
            setPlaying(!playing);
          }}
        >
          {playing ? '暂停动作' : '播放动作'}
        </Button>
        <label htmlFor="skeleton">
          <Switch
            id="skeleton"
            checked={skeleton}
            onCheckedChange={(v) => {
              show.current = v;
              setSkeleton(v);
            }}
          />
          显示骨架
        </label>
        <span>拖动旋转 · 滚轮缩放</span>
      </div>
    </div>
  );
}
