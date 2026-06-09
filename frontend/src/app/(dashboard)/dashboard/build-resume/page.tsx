"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { Sparkles, Loader2 } from "lucide-react";

import StepShell from "@/components/builder/StepShell";
import TagInput from "@/components/builder/TagInput";
import { buildResume, suggestSkills, generatePortfolio, ApiError } from "@/lib/api";
import type { BuildResumeRequest, WorkExperienceInput, ProjectInput } from "@/types";

function emptyWork(): WorkExperienceInput {
  return { company: "", role: "", achievements: "" };
}
function emptyProject(): ProjectInput {
  return { name: "", description: "", tech: [], link: "" };
}

interface FormState {
  personal: { name: string; title: string };
  experience_summary: { years: string; tech_stack: string[] };
  work_experiences: WorkExperienceInput[];
  projects: ProjectInput[];
  education: { degree: string; institution: string; year: string };
  skills: string[];
  social_links: { github: string; linkedin: string; website: string };
  career_goal: string;
}

const INITIAL: FormState = {
  personal: { name: "", title: "" },
  experience_summary: { years: "", tech_stack: [] },
  work_experiences: [emptyWork()],
  projects: [emptyProject()],
  education: { degree: "", institution: "", year: "" },
  skills: [],
  social_links: { github: "", linkedin: "", website: "" },
  career_goal: "",
};

const CLS = {
  input:
    "w-full rounded-xl border border-[var(--pf-border-light)] bg-[var(--pf-surface)] px-4 py-3 text-[var(--pf-text)] placeholder-[var(--pf-muted)] outline-none transition-colors focus:border-[var(--pf-accent)] text-base",
  textarea:
    "w-full rounded-xl border border-[var(--pf-border-light)] bg-[var(--pf-surface)] px-4 py-3 text-[var(--pf-text)] placeholder-[var(--pf-muted)] outline-none transition-colors focus:border-[var(--pf-accent)] text-base resize-none",
  label: "block text-sm font-medium text-[var(--pf-muted)] mb-1.5",
};

export default function BuildResumePage() {
  const { getToken } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState(1);
  const [form, setForm] = useState<FormState>(INITIAL);
  const [submitting, setSubmitting] = useState(false);
  const [suggestingSkills, setSuggestingSkills] = useState(false);

  const totalSteps = 6 + form.work_experiences.length + form.projects.length;
  const next = () => setStep((s) => Math.min(s + 1, totalSteps));
  const back = () => setStep((s) => Math.max(s - 1, 1));

  const addWork = () => setForm(f => ({ ...f, work_experiences: [...f.work_experiences, emptyWork()] }));
  const removeWork = (idx: number) => setForm(f => ({ ...f, work_experiences: f.work_experiences.filter((_, i) => i !== idx) }));
  const addProject = () => setForm(f => ({ ...f, projects: [...f.projects, emptyProject()] }));
  const removeProject = (idx: number) => setForm(f => ({ ...f, projects: f.projects.filter((_, i) => i !== idx) }));

  const patch = useCallback(<K extends keyof FormState>(key: K, val: FormState[K]) => {
    setForm((f) => ({ ...f, [key]: val }));
  }, []);

  const patchWork = (idx: number, field: keyof WorkExperienceInput, val: string) => {
    setForm((f) => {
      const arr = [...f.work_experiences];
      arr[idx] = { ...arr[idx], [field]: val };
      return { ...f, work_experiences: arr };
    });
  };

  const patchProject = (
    idx: number,
    field: keyof Omit<ProjectInput, "tech">,
    val: string,
  ) => {
    setForm((f) => {
      const arr = [...f.projects];
      arr[idx] = { ...arr[idx], [field]: val };
      return { ...f, projects: arr };
    });
  };

  const patchProjectTech = (idx: number, tech: string[]) => {
    setForm((f) => {
      const arr = [...f.projects];
      arr[idx] = { ...arr[idx], tech };
      return { ...f, projects: arr };
    });
  };

  const handleSuggestSkills = async () => {
    setSuggestingSkills(true);
    try {
      const token = await getToken();
      if (!token) return;
      const res = await suggestSkills(
        {
          current_skills: form.skills,
          tech_stack: form.experience_summary.tech_stack,
          role_titles: form.work_experiences.map((w) => w.role).filter(Boolean),
          career_goal: form.career_goal,
        },
        token,
      );
      if (res.suggestions.length) {
        patch("skills", [...form.skills, ...res.suggestions]);
        toast.success(`Added ${res.suggestions.length} skill suggestions!`);
      } else {
        toast.info("No new suggestions — your list looks great!");
      }
    } catch (err) {
      
      if (err instanceof ApiError && err.status === 403) {
        toast.error("AI skill suggestions require the Pro plan.", {
          description: "Upgrade in Settings → Billing to unlock.",
          duration: 7000,
        });
      } else if (err instanceof ApiError) {
        toast.error(err.detail || "Couldn't fetch suggestions.");
      } else {
        toast.error("Couldn't fetch suggestions. Check your connection.");
      }
    } finally {
      setSuggestingSkills(false);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      const payload: BuildResumeRequest = {
        personal: form.personal,
        experience_summary: {
          years: form.experience_summary.years,
          tech_stack: form.experience_summary.tech_stack,
        },
        work_experiences: form.work_experiences.filter((w) => w.company || w.role),
        projects: form.projects.filter((p) => p.name),
        education: form.education,
        skills: form.skills,
        social_links: form.social_links,
        career_goal: form.career_goal,
      };

      const resumeResult = await buildResume(payload, token);
      toast.success("Resume built! Choosing your template…");

      const genResult = await generatePortfolio(resumeResult.resume_id, "aurora", token);
      router.push(`/dashboard/generating/${genResult.portfolio_id}`);
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : "Something went wrong. Please try again.";
      toast.error(msg);
      setSubmitting(false);
    }
  };

  const stepNodes: React.ReactNode[] = [];
  let currentStep = 1;

  stepNodes.push(
    <StepShell
      key="step-1"
      step={currentStep++}
      total={totalSteps}
      emoji="👋"
      question="Let's start with the basics. What's your name?"
      hint="This is how you'll appear at the top of your portfolio."
      onNext={next}
      nextDisabled={!form.personal.name.trim()}
    >
      <div className="space-y-4">
        <div>
          <label className={CLS.label}>Full name</label>
          <input
            autoFocus
            className={CLS.input}
            placeholder="e.g. Alex Johnson"
            value={form.personal.name}
            onChange={(e) => patch("personal", { ...form.personal, name: e.target.value })}
            onKeyDown={(e) => e.key === "Enter" && form.personal.name.trim() && next()}
          />
        </div>
        <div>
          <label className={CLS.label}>Current or desired job title</label>
          <input
            className={CLS.input}
            placeholder="e.g. Senior Full-Stack Engineer"
            value={form.personal.title}
            onChange={(e) => patch("personal", { ...form.personal, title: e.target.value })}
            onKeyDown={(e) => e.key === "Enter" && form.personal.name.trim() && next()}
          />
        </div>
      </div>
    </StepShell>
  );

  stepNodes.push(
    <StepShell
      key="step-2"
      step={currentStep++}
      total={totalSteps}
      emoji="⚡"
      question={`Nice to meet you, ${form.personal.name.split(" ")[0] || "you"}! How much experience do you have?`}
      hint="And what's your primary tech stack?"
      onNext={next}
      onBack={back}
      nextDisabled={!form.experience_summary.years}
    >
      <div className="space-y-5">
        <div>
          <label className={CLS.label}>Years of professional experience</label>
          <div className="grid grid-cols-4 gap-2">
            {["<1", "1-2", "3-5", "6-9", "10-15", "15+", "Student", "Career changer"].map(
              (opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() =>
                    patch("experience_summary", {
                      ...form.experience_summary,
                      years: opt,
                    })
                  }
                  className={`rounded-xl border py-2.5 text-sm font-medium transition-all ${
                    form.experience_summary.years === opt
                      ? "border-[var(--pf-accent)] bg-[var(--pf-accent-soft)] text-[var(--pf-accent-text)]"
                      : "border-[var(--pf-accent-soft)] bg-[var(--pf-surface)] text-[var(--pf-muted)] hover:border-[var(--pf-border-hover)] hover:text-[var(--pf-text)]"
                  }`}
                >
                  {opt}
                </button>
              ),
            )}
          </div>
        </div>
        <div>
          <label className={CLS.label}>Primary tech stack</label>
          <TagInput
            tags={form.experience_summary.tech_stack}
            onChange={(tags) =>
              patch("experience_summary", { ...form.experience_summary, tech_stack: tags })
            }
            placeholder="e.g. React, TypeScript, Node.js — press Enter after each"
          />
          <p className="mt-1.5 text-xs text-[var(--pf-muted)]">Press Enter or comma to add each technology</p>
        </div>
      </div>
    </StepShell>
  );

  form.work_experiences.forEach((exp, index) => {
    stepNodes.push(
      <WorkExpStep
        key={`work-${index}`}
        step={currentStep++}
        total={totalSteps}
        index={index}
        label={index === 0 ? "first" : index === 1 ? "second" : index === 2 ? "third" : "next"}
        data={exp}
        onChange={patchWork}
        onNext={next}
        onBack={back}
        optional={index > 0}
        onAddWork={index === form.work_experiences.length - 1 ? addWork : undefined}
        onRemoveWork={index > 0 ? () => removeWork(index) : undefined}
      />
    );
  });

  form.projects.forEach((proj, index) => {
    stepNodes.push(
      <ProjectStep
        key={`proj-${index}`}
        step={currentStep++}
        total={totalSteps}
        index={index}
        label={index === 0 ? "first" : index === 1 ? "second" : index === 2 ? "third" : "next"}
        data={proj}
        onChangeField={patchProject}
        onChangeTech={patchProjectTech}
        onNext={next}
        onBack={back}
        optional={index > 0}
        onAddProject={index === form.projects.length - 1 ? addProject : undefined}
        onRemoveProject={index > 0 ? () => removeProject(index) : undefined}
      />
    );
  });

  stepNodes.push(
    <StepShell
      key="step-edu"
      step={currentStep++}
      total={totalSteps}
      emoji="🎓"
      question="What's your educational background?"
      hint="Degree, institution, and graduation year. Skip if not applicable."
      onNext={next}
      onBack={back}
    >
      <div className="space-y-4">
        <div>
          <label className={CLS.label}>Degree</label>
          <input
            autoFocus
            className={CLS.input}
            placeholder="e.g. B.Sc. Computer Science, Self-taught, Bootcamp"
            value={form.education.degree}
            onChange={(e) => patch("education", { ...form.education, degree: e.target.value })}
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={CLS.label}>Institution</label>
            <input
              className={CLS.input}
              placeholder="e.g. MIT, Coursera"
              value={form.education.institution}
              onChange={(e) =>
                patch("education", { ...form.education, institution: e.target.value })
              }
            />
          </div>
          <div>
            <label className={CLS.label}>Year</label>
            <input
              className={CLS.input}
              placeholder="e.g. 2021"
              value={form.education.year}
              onChange={(e) =>
                patch("education", { ...form.education, year: e.target.value })
              }
            />
          </div>
        </div>
      </div>
    </StepShell>
  );

  stepNodes.push(
    <StepShell
      key="step-skills"
      step={currentStep++}
      total={totalSteps}
      emoji="🛠️"
      question="What are your key skills?"
      hint="Add the skills you want to highlight. Then let AI suggest what you might be missing."
      onNext={next}
      onBack={back}
      nextDisabled={form.skills.length === 0}
    >
      <div className="space-y-4">
        <TagInput
          tags={form.skills}
          onChange={(tags) => patch("skills", tags)}
          placeholder="e.g. React, Docker, System Design — press Enter after each"
        />
        <button
          type="button"
          onClick={handleSuggestSkills}
          disabled={suggestingSkills}
          className="flex items-center gap-2 rounded-xl border border-[var(--pf-border-medium)] bg-[var(--pf-border-faint)] px-4 py-2.5 text-sm font-medium text-[var(--pf-accent-text)] transition-all hover:border-[rgba(108,99,255,0.5)] hover:bg-[var(--pf-accent-subtle)] disabled:opacity-60"
        >
          {suggestingSkills ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Claude is thinking…
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              AI: suggest skills I might be missing
            </>
          )}
        </button>
        {form.skills.length > 0 && (
          <p className="text-xs text-[var(--pf-muted)]">{form.skills.length} skills added</p>
        )}
      </div>
    </StepShell>
  );

  stepNodes.push(
    <StepShell
      key="step-social"
      step={currentStep++}
      total={totalSteps}
      emoji="🔗"
      question="Where can people find you online?"
      hint="These show up in your portfolio's contact section. All optional."
      onNext={next}
      onBack={back}
    >
      <div className="space-y-4">
        {(
          [
            { key: "github", label: "GitHub", placeholder: "https://github.com/username" },
            {
              key: "linkedin",
              label: "LinkedIn",
              placeholder: "https://linkedin.com/in/username",
            },
            { key: "website", label: "Personal website", placeholder: "https://yoursite.com" },
          ] as const
        ).map(({ key, label, placeholder }) => (
          <div key={key}>
            <label className={CLS.label}>{label}</label>
            <input
              className={CLS.input}
              placeholder={placeholder}
              value={form.social_links[key]}
              onChange={(e) =>
                patch("social_links", { ...form.social_links, [key]: e.target.value })
              }
            />
          </div>
        ))}
      </div>
    </StepShell>
  );

  stepNodes.push(
    <StepShell
      key="step-goal"
      step={currentStep++}
      total={totalSteps}
      emoji="🚀"
      question="Last one! What kind of roles are you targeting?"
      hint="This helps Claude write a compelling summary and tailor your portfolio copy."
      onNext={handleSubmit}
      onBack={back}
      nextLabel="Build my resume with AI ✨"
      nextDisabled={!form.career_goal.trim()}
      loading={submitting}
    >
      <div className="space-y-4">
        <textarea
          autoFocus
          rows={5}
          className={CLS.textarea}
          placeholder={`e.g. "I'm looking for senior frontend roles at product-led startups, ideally working on developer tools or fintech. I love TypeScript and want to lead small teams."`}
          value={form.career_goal}
          onChange={(e) => patch("career_goal", e.target.value)}
        />
        <div className="flex flex-wrap gap-2">
          {[
            "Senior SWE at a startup",
            "Staff engineer at FAANG",
            "Freelance / consulting",
            "First dev job",
            "Engineering manager",
            "Remote-first roles",
          ].map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => {
                const curr = form.career_goal;
                patch(
                  "career_goal",
                  curr
                    ? curr.endsWith(" ")
                      ? curr + suggestion
                      : curr + " " + suggestion
                    : suggestion,
                );
              }}
              className="rounded-full border border-[var(--pf-border-light)] px-3 py-1 text-xs text-[var(--pf-muted)] hover:border-[rgba(108,99,255,0.5)] hover:text-[var(--pf-text)] transition-colors"
            >
              + {suggestion}
            </button>
          ))}
        </div>
      </div>
    </StepShell>
  );

  return (
    <div className="mx-auto max-w-2xl">
      <AnimatePresence mode="wait" initial={false}>
        <div key={step}>{stepNodes[step - 1]}</div>
      </AnimatePresence>
    </div>
  );
}

interface WorkExpStepProps {
  step: number;
  total: number;
  index: number;
  label: string;
  data: WorkExperienceInput;
  onChange: (idx: number, field: keyof WorkExperienceInput, val: string) => void;
  onNext: () => void;
  onBack: () => void;
  optional?: boolean;
  onAddWork?: () => void;
  onRemoveWork?: () => void;
  onAddProject?: () => void;
  onRemoveProject?: () => void;
}

function WorkExpStep({
  step,
  total,
  index,
  label,
  data,
  onChange,
  onNext,

  onBack,
  optional,
  onAddWork,
  onRemoveWork,
}: WorkExpStepProps) {

  const EMOJIS = ["💼", "🏢", "🏗️"];

  return (
    <StepShell
      step={step}
      total={total}
      emoji={EMOJIS[index]}
      question={
        optional
          ? `Any other work experience worth highlighting? (${label})`
          : `Tell me about your ${label} job.`
      }
      hint={optional ? "Skip if you have fewer than 3 roles — just leave it blank." : undefined}
      onNext={onNext}
      onBack={onBack}
      nextDisabled={!optional && !data.company.trim()}
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label
              className="block text-sm font-medium text-[var(--pf-muted)] mb-1.5"
            >
              Company
            </label>
            <input
              autoFocus
              className="w-full rounded-xl border border-[var(--pf-border-light)] bg-[var(--pf-surface)] px-4 py-3 text-[var(--pf-text)] placeholder-[var(--pf-muted)] outline-none transition-colors focus:border-[var(--pf-accent)] text-base"
              placeholder="e.g. Stripe"
              value={data.company}
              onChange={(e) => onChange(index, "company", e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--pf-muted)] mb-1.5">Your role</label>
            <input
              className="w-full rounded-xl border border-[var(--pf-border-light)] bg-[var(--pf-surface)] px-4 py-3 text-[var(--pf-text)] placeholder-[var(--pf-muted)] outline-none transition-colors focus:border-[var(--pf-accent)] text-base"
              placeholder="e.g. Senior Engineer"
              value={data.role}
              onChange={(e) => onChange(index, "role", e.target.value)}
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-[var(--pf-muted)] mb-1.5">
            Key achievements & responsibilities
          </label>
          <textarea
            rows={5}
            className="w-full rounded-xl border border-[var(--pf-border-light)] bg-[var(--pf-surface)] px-4 py-3 text-[var(--pf-text)] placeholder-[var(--pf-muted)] outline-none transition-colors focus:border-[var(--pf-accent)] text-base resize-none"
            placeholder={`e.g.\n• Led migration from monolith to microservices, reducing deploy time by 60%\n• Mentored 3 junior engineers\n• Built real-time dashboard handling 50k events/sec`}
            value={data.achievements}
            onChange={(e) => onChange(index, "achievements", e.target.value)}
          />
          <p className="mt-1.5 text-xs text-[var(--pf-muted)]">
            Claude will expand and polish these into strong bullet points.
          </p>
        </div>
        <div className="flex justify-between">
          {onRemoveWork ? (
            <button type="button" onClick={onRemoveWork} className="text-sm text-red-500 hover:text-red-400">Remove Role</button>
          ) : <div/>}
          {onAddWork ? (
            <button type="button" onClick={onAddWork} className="text-sm text-[var(--pf-accent-text)] hover:text-[#a09cff]">+ Add Another Role</button>
          ) : null}
        </div>
      </div>

    </StepShell>
  );
}

interface ProjectStepProps {
  step: number;
  total: number;
  index: number;
  label: string;
  data: ProjectInput;
  onChangeField: (idx: number, field: keyof Omit<ProjectInput, "tech">, val: string) => void;
  onChangeTech: (idx: number, tech: string[]) => void;
  onNext: () => void;
  onBack: () => void;
  optional?: boolean;
  onAddWork?: () => void;
  onRemoveWork?: () => void;
  onAddProject?: () => void;
  onRemoveProject?: () => void;
}

function ProjectStep({
  step,
  total,
  index,
  label,
  data,
  onChangeField,
  onChangeTech,
  onNext,
  onBack,
  optional,
  onAddProject,
  onRemoveProject,
}: ProjectStepProps) {
  const EMOJIS = ["✨", "🔧", "🎯"];

  const isSkippable = true;

  return (
    <StepShell
      step={step}
      total={total}
      emoji={EMOJIS[index]}
      question={
        optional
          ? `Got another project to show off? (${label})`
          : `What's a project you'd like to feature?`
      }
      hint={
        optional
          ? "Leave blank if you don't have another project."
          : "Add one if you'd like — or skip and come back later."
      }
      onNext={onNext}
      onBack={onBack}
      nextLabel={!data.name.trim() ? "Skip →" : "Continue →"}
      nextDisabled={!isSkippable && !data.name.trim()}
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-[var(--pf-muted)] mb-1.5">Project name</label>
            <input
              autoFocus
              className="w-full rounded-xl border border-[var(--pf-border-light)] bg-[var(--pf-surface)] px-4 py-3 text-[var(--pf-text)] placeholder-[var(--pf-muted)] outline-none transition-colors focus:border-[var(--pf-accent)] text-base"
              placeholder="e.g. VyroPortify"
              value={data.name}
              onChange={(e) => onChangeField(index, "name", e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--pf-muted)] mb-1.5">
              Live link or GitHub
            </label>
            <input
              className="w-full rounded-xl border border-[var(--pf-border-light)] bg-[var(--pf-surface)] px-4 py-3 text-[var(--pf-text)] placeholder-[var(--pf-muted)] outline-none transition-colors focus:border-[var(--pf-accent)] text-base"
              placeholder="https://github.com/…"
              value={data.link}
              onChange={(e) => onChangeField(index, "link", e.target.value)}
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-[var(--pf-muted)] mb-1.5">Description</label>
          <textarea
            rows={3}
            className="w-full rounded-xl border border-[var(--pf-border-light)] bg-[var(--pf-surface)] px-4 py-3 text-[var(--pf-text)] placeholder-[var(--pf-muted)] outline-none transition-colors focus:border-[var(--pf-accent)] text-base resize-none"
            placeholder="What does it do? What problem does it solve? What's the impact?"
            value={data.description}
            onChange={(e) => onChangeField(index, "description", e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-[var(--pf-muted)] mb-1.5">
            Technologies used
          </label>
          <TagInput
            tags={data.tech}
            onChange={(tags) => onChangeTech(index, tags)}
            placeholder="e.g. Next.js, Postgres — press Enter after each"
          />
        </div>

        {}
        <div className="flex justify-between">
          {onRemoveProject ? (
            <button
              type="button"
              onClick={onRemoveProject}
              className="text-sm text-red-500 hover:text-red-400"
            >
              Remove project
            </button>
          ) : (
            <div />
          )}
          {onAddProject ? (
            <button
              type="button"
              onClick={onAddProject}
              className="text-sm text-[var(--pf-accent-text)] hover:text-[#a09cff]"
            >
              + Add another project
            </button>
          ) : null}
        </div>
      </div>
    </StepShell>
  );
}
