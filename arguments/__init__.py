#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use 
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#

from argparse import ArgumentParser, Namespace
import sys
import os


class GroupParams:
    pass


# ParamGroup类用于将类的属性转化为命令行参数，并从解析后的命令行参数中提取这些属性的值
class ParamGroup:
    def __init__(self, parser: ArgumentParser, name: str, fill_none=False):
        group = parser.add_argument_group(name)  # 使用给定的解析器和组名创建一个新的参数组

        for key, value in vars(self).items():  # 遍历类的所有属性和值
            shorthand = False

            if key.startswith("_"):  # 如果属性名以下划线开头
                shorthand = True  # 以下划线开头，表示使用简写形式
                key = key[1:]  # 去掉属性名前面的下划线

            t = type(value)  # 获取属性的类型
            value = value if not fill_none else None  # 如果fill_none为True，将属性值设为None，否则保留原值

            if shorthand:  # 如果使用简写形式
                if t == bool:
                    # 添加布尔型参数，支持长短两种形式
                    group.add_argument("--" + key, ("-" + key[0:1]), default=value, action="store_true")
                else:
                    # 添加其他类型的参数，支持长短两种形式
                    group.add_argument("--" + key, ("-" + key[0:1]), default=value, type=t)
            else:  # 如果不使用简写形式
                if t == bool:
                    # 添加布尔型参数，只支持长形式
                    group.add_argument("--" + key, default=value, action="store_true")
                else:
                    # 添加其他类型的参数，只支持长形式
                    group.add_argument("--" + key, default=value, type=t)

    def extract(self, args):
        """
        提取方法，从命令行参数中提取相应的参数值
        """
        # 创建一个新的GroupParams对象来存储提取的参数
        group = GroupParams()
        # 遍历所有命令行参数
        for arg in vars(args).items():
            # 如果参数名与类的属性名匹配（或带下划线的匹配）
            if arg[0] in vars(self) or ("_" + arg[0]) in vars(self):
                # 将参数值赋给GroupParams对象中的相应属性
                setattr(group, arg[0], arg[1])
        # 返回包含提取参数的GroupParams对象
        return group


class ModelParams(ParamGroup):
    def __init__(self, parser, sentinel=False):
        self.sh_degree = 3
        self._source_path = ""
        self._model_path = ""
        self._images = "images"
        self._resolution = -1
        self._white_background = False
        self.data_device = "cuda"
        self.eval = False
        super().__init__(parser, "Loading Parameters", sentinel)

    def extract(self, args):
        g = super().extract(args)
        g.source_path = os.path.abspath(g.source_path)
        return g


class PipelineParams(ParamGroup):
    def __init__(self, parser):
        self.convert_SHs_python = False
        self.compute_cov3D_python = False
        self.debug = False
        super().__init__(parser, "Pipeline Parameters")


class OptimizationParams(ParamGroup):
    def __init__(self, parser):
        self.iterations = 30_000
        self.position_lr_init = 0.00016
        self.position_lr_final = 0.0000016
        self.position_lr_delay_mult = 0.01
        self.position_lr_max_steps = 30_000
        self.feature_lr = 0.0025
        self.opacity_lr = 0.05
        self.scaling_lr = 0.005
        self.rotation_lr = 0.001
        self.percent_dense = 0.01
        self.lambda_dssim = 0.2
        self.densification_interval = 100
        self.opacity_reset_interval = 3000
        self.densify_from_iter = 500
        self.densify_until_iter = 15_000
        self.densify_grad_threshold = 0.0002
        self.random_background = False
        super().__init__(parser, "Optimization Parameters")


def get_combined_args(parser: ArgumentParser):
    # 获取命令行参数（去掉脚本名）
    cmdlne_string = sys.argv[1:]
    # 初始化配置文件参数字符串为默认的空Namespace
    cfgfile_string = "Namespace()"
    # 解析命令行参数
    args_cmdline = parser.parse_args(cmdlne_string)

    try:
        # 获取配置文件路径（假设配置文件位于模型路径下的cfg_args文件）
        cfgfilepath = os.path.join(args_cmdline.model_path, "cfg_args")
        print("Looking for config file in", cfgfilepath)
        # 打开并读取配置文件内容
        with open(cfgfilepath) as cfg_file:
            print("Config file found: {}".format(cfgfilepath))
            cfgfile_string = cfg_file.read()
    except TypeError:
        # 如果出现TypeError异常，表示未找到配置文件（这里似乎没有写完整）
        print("Config file not found at")
        pass

    # 将配置文件字符串解析为Namespace对象
    args_cfgfile = eval(cfgfile_string)

    # 将配置文件参数转换为字典
    merged_dict = vars(args_cfgfile).copy()
    # 遍历命令行参数，如果命令行参数不为None，则覆盖配置文件中的对应参数
    for k, v in vars(args_cmdline).items():
        if v != None:
            merged_dict[k] = v
    # 返回合并后的Namespace对象
    # 注：
    # Namespace 是 argparse 模块中的一个类，用于保存解析后的命令行参数。它将命令行参数作为对象的属性，提供了一个方便的方式来访问这些参数。
    return Namespace(**merged_dict)
