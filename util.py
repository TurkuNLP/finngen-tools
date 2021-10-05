import math

from transformers.trainer_callback import TrainerCallback


class StopOnNonFiniteCallback(TrainerCallback):
    def on_evaluate(self, args, state, control, metrics, **kwargs):
        metric = 'eval_loss'
        value = metrics.get(metric)

        if value is None:
            raise ValueError(f'did not find {metric}')

        if math.isinf(value) or math.isnan(value):
            logger.warning(f'{metric} not finite, stopping: {value}')
            control.should_training_stop = True
