import { useProjectStore } from "@/store/use-project-store";

describe("Sprint F5: Research Workspace & Project Platform Verification", () => {
  beforeEach(() => {
    useProjectStore.setState({
      projects: [],
      tasks: [],
      notes: [],
      reports: [],
      selectedProjectId: null,
    });
  });

  it("adds a new research project to state correctly", () => {
    const mockProject = {
      id: "prj_test_1",
      title: "Gene Editing Benchmark Project",
      description: "Testing Cas9 variants",
      ai_summary: "Initial workspace summary",
      status: "active" as const,
      domain: "Biomedical & Genomics",
      document_count: 5,
      task_count: 2,
      updated_at: new Date().toISOString(),
    };

    useProjectStore.getState().addProject(mockProject);

    const projects = useProjectStore.getState().projects;
    expect(projects).toHaveLength(1);
    expect(projects[0].title).toBe("Gene Editing Benchmark Project");
  });

  it("adds and advances project task status cleanly", () => {
    const task = {
      id: "tsk_test_1",
      project_id: "prj_test_1",
      title: "Perform sequence alignment",
      status: "todo" as const,
      priority: "high" as const,
    };

    useProjectStore.getState().addTask(task);
    expect(useProjectStore.getState().tasks[0].status).toBe("todo");

    useProjectStore.getState().updateTaskStatus("tsk_test_1", "in_progress");
    expect(useProjectStore.getState().tasks[0].status).toBe("in_progress");

    useProjectStore.getState().updateTaskStatus("tsk_test_1", "done");
    expect(useProjectStore.getState().tasks[0].status).toBe("done");
  });

  it("saves and updates project Markdown notes", () => {
    const note = {
      id: "note_test_1",
      project_id: "prj_test_1",
      title: "Initial Hypothesis Notes",
      content: "# Cas9 Notes\n- Verified high specificity.",
      updated_at: new Date().toISOString(),
    };

    useProjectStore.getState().saveNote(note);

    const notes = useProjectStore.getState().notes;
    expect(notes).toHaveLength(1);
    expect(notes[0].content).toContain("Cas9 Notes");
  });
});
