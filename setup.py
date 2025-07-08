import os
import platform
import subprocess
from setuptools import setup
from setuptools.command.build_py import build_py

try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    # 如果wheel包不可用，回退到基本实现
    bdist_wheel = None

# 定义Go共享库的名称，根据不同操作系统而变化
LIB_NAME = "librenderer.so"
if platform.system() == "Windows":
    LIB_NAME = "renderer.dll"
elif platform.system() == "Darwin":  # macOS
    LIB_NAME = "librenderer.dylib"  # macOS 惯例使用 .dylib


class CustomBuildWheel(bdist_wheel):
    """自定义wheel构建类,确保生成平台特定但兼容性更好的wheel"""
    
    def finalize_options(self) -> None:
        super().finalize_options()
        # 强制生成平台特定的wheel，而不是通用wheel
        self.root_is_pure = False
    
    def get_tag(self) -> tuple[str, str, str]:
        # 获取平台特定的标签，但使用更通用的版本要求
        python, abi, plat = super().get_tag()
        
        # 为不同平台设置更宽松的兼容性要求
        if plat.startswith('macosx'):
            # 对于macOS，使用合理的最低版本要求
            if 'arm64' in plat:
                plat = 'macosx_12_0_arm64'  # Apple Silicon，macOS 12+ (合理的现代要求)
            elif 'x86_64' in plat:
                plat = 'macosx_11_0_x86_64'  # Intel Mac，macOS 11+ (仍保持较好兼容性)
        elif plat.startswith('linux'):
            # 对于Linux，使用manylinux标签以获得更好的兼容性
            if 'x86_64' in plat:
                plat = 'manylinux1_x86_64'  # x86_64架构
            elif 'aarch64' in plat:
                plat = 'manylinux2014_aarch64'  # ARM64架构，需要更新的manylinux标准
            elif 'arm' in plat and 'v7' in plat:
                plat = 'manylinux2014_armv7l'  # ARM v7架构
            elif 'i386' in plat or 'i686' in plat:
                plat = 'manylinux1_i686'  # 32位x86架构
        elif plat.startswith('win'):
            # Windows平台标签
            if 'amd64' in plat or 'x86_64' in plat:
                plat = 'win_amd64'  # 64位x86架构
            elif 'arm64' in plat:
                plat = 'win_arm64'  # ARM64架构（Windows on ARM）
            elif 'win32' in plat or 'i386' in plat:
                plat = 'win32'  # 32位x86架构
            
        return python, abi, plat


class CustomBuild(build_py):
    """自定义构建类,在构建Python包之前先编译Go代码。"""

    def run(self) -> None:
        print("--- Running custom Go build command ---")

        # 定义Go源文件和目标库文件的路径
        go_src_path = os.path.join(os.path.dirname(__file__), "cognihub_pygotemplate", "renderer.go")
        lib_output_path = os.path.join(os.path.dirname(__file__), "cognihub_pygotemplate", LIB_NAME)

        if not os.path.exists(go_src_path):
            raise FileNotFoundError(f"Go source file not found at: {go_src_path}")

        # 构建 go build 命令
        command = [
            "go",
            "build",
            "-buildmode=c-shared",
            "-o",
            lib_output_path,
            go_src_path,
        ]

        try:
            # 执行编译命令
            print(f"Executing command: {' '.join(command)}")
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            print(f"Successfully compiled Go code to {lib_output_path}")
        except FileNotFoundError:
            raise RuntimeError(
                "Go compiler not found. Please make sure Go is installed and in your system's PATH."
            )
        except subprocess.CalledProcessError as e:
            # 如果编译失败，打印详细的错误信息
            error_message = (
                "Failed to compile Go source.\n"
                f"Command: {' '.join(e.cmd)}\n"
                f"Return Code: {e.returncode}\n"
                f"Stderr:\n{e.stderr}"
            )
            raise RuntimeError(error_message) from e

        # 执行原始的 build_py 命令，继续Python部分的构建
        super().run()


# 使用 setup() 函数来配置项目
cmdclass_dict = {'build_py': CustomBuild}

# 只有当wheel可用时才添加自定义wheel命令
if bdist_wheel is not None:
    cmdclass_dict['bdist_wheel'] = CustomBuildWheel

setup(
    # cmdclass 参数告诉 setuptools 使用我们的自定义类来执行命令
    cmdclass=cmdclass_dict,
    # 将编译好的共享库包含在包数据中，这样它才会被一起安装
    package_data={
        "cognihub_pygotemplate": [
            "librenderer.so",      # Linux
            "librenderer.dylib",   # macOS  
            "renderer.dll",        # Windows
        ],
    },
    # 明确指出这不是纯Python包
    zip_safe=False,
)
