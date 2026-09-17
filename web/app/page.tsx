import { useEffect, useState } from 'react';
import { asset } from '@/lib/asset';
import {
  ArrowDownToLine,
  ArrowUpRight,
  Check,
  Film,
  Layers3,
  Terminal,
  Rotate3d,
} from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import RigViewer from './rig-viewer';
type Log = {
  time: string;
  stage: string;
  event: string;
  status?: string;
  progress?: number;
  parameters?: unknown;
};
type Project = {
  ready: boolean;
  updated: string;
  events: Log[];
  steps: {
    id: string;
    title: string;
    detail: string;
    status: string;
    progress: number;
  }[];
  files: { name: string; url: string; bytes: number }[];
  video_report?: {
    duration: number;
    width: number;
    height: number;
    fps: number;
  };
};
export default function Home() {
  const [data, setData] = useState<Project | null>(null),
    [error, setError] = useState(''),
    [tab, setTab] = useState('film');
  useEffect(() => {
    const load = () =>
      fetch(asset('/data/project.json'), { cache: 'no-store' })
        .then((r) => {
          if (!r.ok) throw Error('制作档案暂时无法读取');
          return r.json();
        })
        .then((d) => {
          setData(d as Project);
          setError('');
        })
        .catch((e) => setError(e.message));
    void load();
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, []);
  const has = (s: string) => data?.files.some((f) => f.url.endsWith(s));
  const done = data?.steps.filter((s) => s.status === 'SUCCEEDED').length || 0;
  return (
    <main className="studio">
      <header className="topbar">
        <div className="brand">
          <span className="brand-seal">玄</span>
          <span>
            玄银 <small>MOTION ARCHIVE / 001</small>
          </span>
        </div>
        <div className="top-meta">
          <span className="live-dot" />
          {data?.ready ? '制作完成' : '制作进行中'}
          <span className="divider" />
          MESHY × BLENDER
        </div>
      </header>
      <section className="project-heading">
        <div>
          <p className="eyebrow">CHARACTER & MOTION STUDY</p>
          <h1>
            以静制动。<span>太极 · 云手</span>
          </h1>
        </div>
        <p className="project-note">
          黑衣、银饰与流动的身形。
          <br />
          从角色重建到最终成片的制作档案。
        </p>
      </section>
      {error && (
        <p role="alert" className="error">
          {error}。请刷新重试。
        </p>
      )}
      <div className="workspace">
        <section className="main-panel">
          <Tabs value={tab} onValueChange={(v) => setTab(String(v))}>
            <div className="panel-top">
              <TabsList variant="line" className="view-tabs">
                <TabsTrigger value="film">
                  <Film size={16} />
                  成片
                </TabsTrigger>
                <TabsTrigger value="rig">
                  <Rotate3d size={16} />
                  骨骼与动作
                </TabsTrigger>
                <TabsTrigger value="character">
                  <Layers3 size={16} />
                  角色
                </TabsTrigger>
              </TabsList>
              <span className="small-mono">CLOUD HANDS</span>
            </div>
            <TabsContent value="film">
              <div className="screen">
                {data?.ready ? (
                  <video
                    controls
                    playsInline
                    preload="metadata"
                    poster={asset('/media/poster.jpg')}
                    src={asset('/media/taichi_final.mp4')}
                    aria-label="玄银太极 Blender 渲染成片"
                  >
                    <track
                      kind="captions"
                      src={asset('/media/taichi.vtt')}
                      srcLang="zh"
                      label="画面描述"
                    />
                  </video>
                ) : (
                  <div className="work-in-progress">
                    {has('character_preview.png') ? (
                      <img
                        width={512}
                        height={512}
                        src={asset('/media/character_preview.png')}
                        alt="Meshy 角色"
                      />
                    ) : has('geometry_preview.png') ? (
                      <img
                        width={512}
                        height={512}
                        src={asset('/media/geometry_preview.png')}
                        alt="角色几何"
                      />
                    ) : null}
                    <p>正在制作成片</p>
                    <span>下方记录显示每一步的实际进度。</span>
                  </div>
                )}
              </div>
            </TabsContent>
            <TabsContent value="rig">
              <div className="screen">
                {has('character.glb') ? (
                  <RigViewer />
                ) : (
                  <div className="work-in-progress">
                    <p>骨架与动作准备中</p>
                    <span>完成后可旋转查看角色，并切换骨架显示。</span>
                  </div>
                )}
              </div>
            </TabsContent>
            <TabsContent value="character">
              <div className="screen character-screen">
                {has('character_preview.png') ? (
                  <img
                    width={512}
                    height={512}
                    src={asset('/media/character_preview.png')}
                    alt="黑发、黑衣、银饰的卡通女性角色"
                  />
                ) : null}
                <div className="character-caption">
                  <span>01 / 角色设定</span>
                  <h2>玄银</h2>
                  <p>
                    女性 · 轻卡通风格
                    <br />
                    黑色太极服 / 黑发 / 银色配饰
                  </p>
                </div>
              </div>
            </TabsContent>
          </Tabs>
          <div className="screen-footer">
            <span>
              <i className="live-dot" />
              {data?.ready ? 'BLENDER RENDER' : 'PRODUCTION IN PROGRESS'}
            </span>
            <span>
              {data?.video_report
                ? `${data.video_report.width} × ${data.video_report.height} · ${data.video_report.fps} FPS · ${data.video_report.duration.toFixed(1)} 秒`
                : '角色 → 骨架 → 动作 → 渲染'}
            </span>
          </div>
          <div className="downloads">
            {data?.files
              .filter((f) => !f.url.endsWith('.png') && !f.url.endsWith('.jpg'))
              .map((f) => (
                <a key={f.url} href={asset(f.url)} download>
                  <ArrowDownToLine size={17} />
                  {f.name}
                  <small>{(f.bytes / 1048576).toFixed(1)} MB</small>
                </a>
              ))}
          </div>
        </section>
        <aside className="process-panel">
          <div className="section-title">
            <h2>制作进程</h2>
            <span className="small-mono">
              {String(done).padStart(2, '0')} / 07
            </span>
          </div>
          <Progress
            value={(done / 7) * 100}
            aria-label="制作完成比例"
            className="total-progress"
          />
          <ol className="process-list">
            {data?.steps.map((s, i) => (
              <li
                key={s.id}
                className={
                  s.status === 'SUCCEEDED'
                    ? 'complete'
                    : s.status === 'IN_PROGRESS'
                      ? 'active'
                      : ''
                }
              >
                <span className="step-icon">
                  {s.status === 'SUCCEEDED' ? (
                    <Check size={15} />
                  ) : (
                    String(i + 1).padStart(2, '0')
                  )}
                </span>
                <div>
                  <h3>
                    {s.title}
                    <span>
                      {s.status === 'SUCCEEDED'
                        ? '完成'
                        : s.status === 'IN_PROGRESS'
                          ? `${s.progress}%`
                          : '待开始'}
                    </span>
                  </h3>
                  <p>{s.detail}</p>
                </div>
              </li>
            ))}
          </ol>
          <div className="production-note">
            <span className="eyebrow">运动如何发生</span>
            <p>
              Meshy 生成角色和骨架。太极动作重定向为骨骼关键帧，再在 Blender
              中调整时间、布光并逐帧渲染。
            </p>
            <span className="annotation">
              骨骼驱动的三维动画 · 可在 3D 视图检查
            </span>
          </div>
        </aside>
      </div>
      <section className="record-section">
        <div className="section-title">
          <div>
            <p className="eyebrow">PRODUCTION JOURNAL</p>
            <h2>每一步，都有记录。</h2>
          </div>
          <a className="text-link" href={asset('/data/events.json')} download>
            导出日志 <ArrowUpRight size={16} />
          </a>
        </div>
        <div className="journal-grid">
          <div className="log-panel">
            <div className="log-heading">
              <Terminal size={16} />
              运行日志<span>UTC</span>
            </div>
            <div className="log-entries">
              {data?.events
                .slice()
                .reverse()
                .map((e, i) => (
                  <details key={`${e.time}-${i}`} className="log-entry">
                    <summary>
                      <time>
                        {new Date(e.time).toLocaleTimeString('en-GB', {
                          timeZone: 'UTC',
                        })}
                      </time>
                      <span
                        className={e.status === 'SUCCEEDED' ? 'success' : ''}
                      >
                        {e.stage}
                      </span>
                      <span>
                        {e.status || e.event}
                        {e.progress !== undefined ? ` · ${e.progress}%` : ''}
                      </span>
                    </summary>
                    <pre>{JSON.stringify(e, null, 2)}</pre>
                  </details>
                ))}
            </div>
          </div>
          <div className="method-panel">
            <h3>制作方法与源文件</h3>
            <p>
              提示词、任务进度与参数保存在日志中。脚本覆盖角色生成、场景搭建、渲染和视频编码，可用于复现或修改作品。
            </p>
            {[
              ['meshy_pipeline.py', '01　Meshy 生成与绑定'],
              ['build_scene.py', '02　Blender 场景与骨架动画'],
              ['render_frames.py', '03　逐帧渲染'],
              ['encode_video.py', '04　视频编码'],
              ['README.md', '完整制作说明'],
            ].map(([file, label]) => (
              <a key={file} href={asset('/source/' + file)} download>
                {label}
                <ArrowDownToLine size={16} />
              </a>
            ))}
            <p className="annotation">
              密钥与临时下载凭据保留在本地，不包含在网页和导出日志中。
            </p>
          </div>
        </div>
        {has('contact_sheet.jpg') && (
          <figure className="contact-sheet">
            <img
              width={1440}
              height={600}
              src={asset('/media/contact_sheet.jpg')}
              alt="太极关键帧检查图"
              loading="lazy"
            />
            <figcaption>关键帧检查 / 动作姿态与画面连续性</figcaption>
          </figure>
        )}
      </section>
      <footer className="page-footer">
        <span>玄银 / SILVER IN MOTION</span>
        <span>Meshy → Skeleton → Blender</span>
      </footer>
    </main>
  );
}
