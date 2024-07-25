# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
from megatron.core.optimizer import OptimizerConfig

from nemo.collections.llm.utils import Config


class Basic:
    def __init__(
        self,
        name: str = None,
        version: int = None,
        size: int = None,
        measure: str = "B",
        cfg: dict = {},
    ):
        """
        :param str name: model name.
        :param int version: model version.
        :param int size: model size.
        :param str measure: meausre of model size. "M" if model size in millions, "B" if in billions.
        :param dict cfg: auto configurator runner config.
        """

        self.name = name
        self.version = version
        self.size = size
        self.measure = measure
        self.cfg = cfg
        self.num_nodes = cfg.get("num_nodes")
        self.num_gpus = cfg.get("gpu_count")
        self.max_steps = cfg.get("max_steps_per_run")
        self.seq_length = cfg.get("seq_length")
        self.global_batch_size = cfg.get("global_batch_size")
        self.tokenizer_path = cfg.get("tokenizer_path")
        self.data_paths = cfg.get("data_paths")
        self.weights = self._get_data_weights()

    def model_config(self):
        """Function that returns model config."""

        None

    def tokenizer_config(self):
        """Function that returns tokenizer config."""

        None

    def get_optim_config(self) -> OptimizerConfig:
        """
        Function that returns optimizer config.
        :return: optim config.
        :rtype: OptimizerConfig.
        """

        optim_config = Config(
            OptimizerConfig,
            optimizer='adam',
            lr=1e-4,
            min_lr=1e-5,
            use_distributed_optimizer=True,
            bf16=True,
            adam_beta1=0.9,
            adam_beta2=0.95,
            overlap_grad_reduce=False,
            overlap_param_gather=True,
        )

        return optim_config

    def get_trainer_config(self) -> dict:
        """
        Function that returns config for PTL trainer.
        :return: trainer config.
        :rtype: dict.
        """

        trainer_config = {
            "accelerator": "gpu",
            "precision": "bf16",
            "logger": False,
            "enable_checkpointing": False,
            "use_distributed_sampler": False,
            "max_epochs": None,
            "log_every_n_steps": 1,
            "limit_val_batches": 1,
            "limit_test_batches": 1,
            "accumulate_grad_batches": 1,
            "gradient_clip_val": 1.0,
            "num_nodes": self.num_nodes,
            "devices": self.num_gpus,
            "max_steps": self.max_steps,
            "val_check_interval": self.max_steps,
        }

        return trainer_config

    def get_data_config(self) -> dict:
        """
        Function that returns dataset config.
        :return: data config.
        :rtype: dict.
        """

        data_config = {
            "paths": self.data_paths,
            "weights": self.weights,
            "seq_length": self.seq_length,
            "global_batch_size": self.global_batch_size,
            "num_workers": 2,
            "split": "99990,8,2",
            "index_mapping_dir": None,
        }

        return data_config

    def get_run_config(self) -> dict:
        """
        Function that returns config for cluster job.
        :return: cluster job config.
        :rtype: dict.
        """

        run_config = {
            "name": f"{self.name}_{self.size}{self.measure}",
            "results_dir": None,
            "time_limit": "0-00:30:00",
        }

        return run_config

    def _get_data_weights(self) -> list:
        """
        Function that returns weights for train dataset.
        :return: list of data weights.
        :rtype: list.
        """

        if not self.data_paths:
            return None

        datafiles_num = len(self.data_paths)
        weight = np.round(1 / datafiles_num, 2)
        weights = [float(weight)] * datafiles_num

        return weights