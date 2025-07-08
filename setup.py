import os
import platform
import subprocess
import shutil
import glob
from setuptools import setup
from setuptools.command.build_py import build_py
from distutils.command.clean import clean
from distutils.cmd import Command

try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    # 如果wheel包不可用，回退到基本实现
    bdist_wheel = None

try:
    import coverage
    coverage_available = True
except ImportError:
    # 如果coverage包不可用，回退到基本unittest
    coverage_available = False

try:
    import mypy
    mypy_available = True
except ImportError:
    # 如果mypy包不可用，跳过类型检查
    mypy_available = False

# 定义Go共享库的名称，根据不同操作系统而变化
LIB_NAME = "librenderer.so"
if platform.system() == "Windows":
    LIB_NAME = "renderer.dll"
elif platform.system() == "Darwin":  # macOS
    LIB_NAME = "librenderer.dylib"  # macOS 惯例使用 .dylib


class CustomClean(clean):
    """自定义清理命令,清理所有构建产物包括Go编译的文件"""
    
    def run(self)->None:
        print("🧹 Cleaning build artifacts...")
        
        # 执行默认的clean操作
        super().run()
        
        # 清理Go编译生成的文件
        go_files = [
            "cognihub_pygotemplate/librenderer.dylib",  # macOS
            "cognihub_pygotemplate/librenderer.so",     # Linux  
            "cognihub_pygotemplate/renderer.dll",       # Windows
            "cognihub_pygotemplate/librenderer.h"       # Header file
        ]
        
        for file_path in go_files:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"  🗑️  Removed {file_path}")
        
        # 清理Python缓存文件
        cache_removed = 0
        for root, dirs, files in os.walk("."):
            # 移除.pyc文件
            for file in files:
                if file.endswith(".pyc"):
                    os.remove(os.path.join(root, file))
                    cache_removed += 1
            
            # 移除__pycache__目录
            if "__pycache__" in dirs:
                pycache_path = os.path.join(root, "__pycache__")
                shutil.rmtree(pycache_path)
                dirs.remove("__pycache__")  # 不再遍历它
                cache_removed += 1
        
        if cache_removed > 0:
            print(f"  🗑️  Removed {cache_removed} Python cache files/directories")
        
        # 清理egg-info目录
        for egg_info in glob.glob("*.egg-info"):
            if os.path.exists(egg_info):
                shutil.rmtree(egg_info)
                print(f"  🗑️  Removed {egg_info}")
        
        # 清理build和dist目录
        build_dirs = ["build", "dist"]
        for dir_name in build_dirs:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
                print(f"  🗑️  Removed {dir_name}/")
        
        # 清理覆盖度报告文件（仅当coverage可用时）
        if coverage_available:
            coverage_files = [".coverage", "htmlcov"]
            for item in coverage_files:
                if os.path.exists(item):
                    if os.path.isfile(item):
                        os.remove(item)
                        print(f"  🗑️  Removed {item}")
                    elif os.path.isdir(item):
                        shutil.rmtree(item)
                        print(f"  🗑️  Removed {item}/")
        
        # 清理mypy缓存（仅当mypy可用时）
        if mypy_available:
            mypy_cache = ".mypy_cache"
            if os.path.exists(mypy_cache):
                shutil.rmtree(mypy_cache)
                print(f"  🗑️  Removed {mypy_cache}/")
        
        print("✅ Clean completed!")


class CustomTest(Command):
    """自定义测试命令,运行unittest discover"""
    
    description = 'run unit tests'
    user_options: list[tuple[str, str]] = []

    def initialize_options(self)->None:
        pass

    def finalize_options(self)->None:
        pass
    
    def run(self)->None:
        if coverage_available:
            print("🧪 Running unit tests with coverage...")
            
            # 运行coverage erase清理之前的数据
            subprocess.run(["python", "-m", "coverage", "erase"], capture_output=True)
            
            # 运行coverage run
            result = subprocess.run([
                "python", "-m", "coverage", "run", 
                "--source=cognihub_pygotemplate",
                "--omit=*/tests/*,*/test_*",
                "-m", "unittest", "discover", 
                "-s", "tests", "-p", "test_*.py", "-v"
            ])
            
            if result.returncode == 0:
                print("✅ Tests completed successfully!")
                
                # 生成覆盖度报告
                print("\n📊 Coverage Report:")
                print("=" * 50)
                subprocess.run(["python", "-m", "coverage", "report", "-m"])
                
                # 生成HTML报告
                html_result = subprocess.run([
                    "python", "-m", "coverage", "html", 
                    "--directory=htmlcov"
                ], capture_output=True)
                
                if html_result.returncode == 0:
                    print("\n📄 HTML coverage report generated in 'htmlcov/' directory")
                    print("   Open 'htmlcov/index.html' in your browser to view detailed coverage")
                
            else:
                print("❌ Tests failed!")
                raise SystemExit(result.returncode)
        else:
            print("🧪 Running unit tests...")
            print("� Install 'coverage' package for code coverage analysis: pip install coverage")
            
            # 运行基本的unittest
            result = subprocess.run([
                "python", "-m", "unittest", "discover", 
                "-s", "tests", "-p", "test_*.py", "-v"
            ])
            
            if result.returncode == 0:
                print("✅ Tests completed successfully!")
            else:
                print("❌ Tests failed!")
                raise SystemExit(result.returncode)


class CustomTypeCheck(Command):
    """自定义类型检查命令,运行mypy进行静态类型检查"""
    
    description = 'run static type checking with mypy'
    user_options = [
        ('strict', None, 'run mypy in strict mode'),
        ('package=', 'p', 'specify package to check (default: cognihub_pygotemplate)'),
    ]

    def initialize_options(self)->None:
        self.strict = False
        self.package = 'cognihub_pygotemplate'

    def finalize_options(self)->None:
        pass
    
    def run(self)->None:
        if mypy_available:
            print("🔍 Running static type checking with mypy...")
            
            # 构建mypy命令
            cmd = ["python", "-m", "mypy"]
            
            # 添加基本选项
            cmd.extend([
                "--show-error-codes",
                "--no-error-summary"
            ])
            
            # 如果指定了strict模式
            if self.strict:
                cmd.append("--strict")
                print("   Using strict mode")
            else:
                # 使用相对宽松但仍然有用的配置
                cmd.extend([
                    "--warn-unused-ignores",
                    "--warn-redundant-casts",
                    "--warn-return-any",
                    "--check-untyped-defs"
                ])
            
            # 添加要检查的包/目录
            cmd.append(self.package)
            
            print(f"   Checking package: {self.package}")
            
            # 运行mypy
            result = subprocess.run(cmd)
            
            if result.returncode == 0:
                print("✅ Type checking completed successfully!")
                print("   No type errors found.")
            else:
                print("⚠️  Type checking completed with issues.")
                print("   See output above for details.")
                # 不抛出异常，只是报告问题
        else:
            print("🔍 Running static type checking...")
            print("💡 Install 'mypy' package for static type analysis: pip install mypy")
            print("   Skipping type checking...")


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
cmdclass_dict = {
    'build_py': CustomBuild,
    'clean': CustomClean,
    'test': CustomTest,
    'typecheck': CustomTypeCheck
}

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
