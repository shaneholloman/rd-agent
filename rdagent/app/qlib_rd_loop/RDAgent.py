import pickle
from rdagent.app.qlib_rd_loop.conf import PROP_SETTING
from rdagent.core.proposal import (
    Hypothesis2Experiment,
    HypothesisExperiment2Feedback,
    HypothesisGen,
    Trace,
)
from rdagent.core.scenario import Scenario
from rdagent.core.task_generator import TaskGenerator
from rdagent.core.utils import import_class

class Model_RD_Agent:
    def __init__(self):
        self.scen: Scenario = import_class(PROP_SETTING.qlib_model_scen)()
        self.hypothesis_gen: HypothesisGen = import_class(PROP_SETTING.qlib_model_hypothesis_gen)(self.scen)
        self.hypothesis2experiment: Hypothesis2Experiment = import_class(PROP_SETTING.qlib_model_hypothesis2experiment)()
        self.qlib_model_coder: TaskGenerator = import_class(PROP_SETTING.qlib_model_coder)(self.scen)
        self.qlib_model_runner: TaskGenerator = import_class(PROP_SETTING.qlib_model_runner)(self.scen)
        self.qlib_model_summarizer: HypothesisExperiment2Feedback = import_class(PROP_SETTING.qlib_model_summarizer)(self.scen)
        self.trace = Trace(scen=self.scen)

    def generate_hypothesis(self):
        hypothesis = self.hypothesis_gen.gen(self.trace)
        self.dump_objects(hypothesis=hypothesis, trace=self.trace, filename='step_hypothesis.pkl')
        return hypothesis

    def convert_hypothesis(self, hypothesis):
        exp = self.hypothesis2experiment.convert(hypothesis, self.trace)
        self.dump_objects(exp=exp, hypothesis=hypothesis, trace=self.trace, filename='step_experiment.pkl')
        return exp

    def generate_code(self, exp):
        exp = self.qlib_model_coder.generate(exp)
        self.dump_objects(exp=exp, trace=self.trace, filename='step_code.pkl')
        return exp

    def run_experiment(self, exp):
        exp = self.qlib_model_runner.generate(exp)
        self.dump_objects(exp=exp, trace=self.trace, filename='step_run.pkl')
        return exp

    def generate_feedback(self, exp, hypothesis):
        feedback = self.qlib_model_summarizer.generateFeedback(exp, hypothesis, self.trace)
        self.dump_objects(exp=exp, hypothesis=hypothesis, feedback=feedback, trace=self.trace, filename='step_feedback.pkl')
        return feedback

    def append_to_trace(self, hypothesis, exp, feedback):
        self.trace.hist.append((hypothesis, exp, feedback))
        self.dump_objects(trace=self.trace, filename='step_trace.pkl')

    def dump_objects(self, exp=None, hypothesis=None, feedback=None, trace=None, filename='dumped_objects.pkl'):
        with open(filename, 'wb') as f:
            pickle.dump((exp, hypothesis, feedback, trace or self.trace), f)

    def load_objects(self, filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)

def process_steps(agent):
    # Load trace if available
    try:
        _, _, _, trace = agent.load_objects('step_trace.pkl')
        agent.trace = trace
        print(trace)
    except FileNotFoundError:
        pass

    # Step 1: Generate hypothesis
    try:
        _, hypothesis, _, _ = agent.load_objects('step_hypothesis.pkl')
    except FileNotFoundError:
        hypothesis = agent.generate_hypothesis()

    # Step 2: Convert hypothesis
    try:
        exp, _, _, _ = agent.load_objects('step_experiment.pkl')
    except FileNotFoundError:
        exp = agent.convert_hypothesis(hypothesis)

    # Step 3: Generate code
    try:
        exp, _, _, _ = agent.load_objects('step_code.pkl')
    except FileNotFoundError:
        exp = agent.generate_code(exp)

    # Step 4: Run experiment
    try:
        exp, _, _, _ = agent.load_objects('step_run.pkl')
    except FileNotFoundError:
        exp = agent.run_experiment(exp)

    # Step 5: Generate feedback
    # try:
    #     _, _, feedback, _ = agent.load_objects('step_feedback.pkl')
    # except FileNotFoundError:
    feedback = agent.generate_feedback(exp, hypothesis)

    # Step 6: Append to trace
    agent.append_to_trace(hypothesis, exp, feedback)

if __name__ == "__main__":
    agent = Model_RD_Agent()
    process_steps(agent)
