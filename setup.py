from distutils.core import setup

long_description = """# JustStart: A Customizable Cross-Platform Local Service Manager

JustStart is a highly customizable, extensible, and cross-platform local service manager that supports user-defined running conditions, nested inheritance of environment variables, runtime variables, and running configurations.

With JustStart, you can easily manage your services across different platforms such as Windows, macOS, and Linux, providing a consistent experience and powerful customization options.

## Key Features

- **User-defined running conditions**: Define your own conditions to control when and how your services are started, stopped, or restarted.
- **Nested inheritance of environment variables**: JustStart allows you to inherit environment variables from parent to child services, providing a flexible and modular way to configure your services.
- **Runtime variables and running configurations**: Enjoy the flexibility of managing your services with customizable runtime variables and running configurations, tailoring each service to your specific needs.
- **Cross-platform compatibility**: JustStart is designed to work seamlessly across Windows, macOS, and Linux, providing you with a consistent management experience regardless of the platform you are using.

## Getting Started

To get started with JustStart, install the package and refer to the provided documentation to learn about configuring and managing your services.

Whether you are a developer looking to streamline your local services or a system administrator managing multiple services across different platforms, JustStart provides a powerful and flexible solution to meet your needs.
"""

setup(
    name="juststart",
    version="0.1.0",
    author="XZ",
    author_email="xiangzhedev@gmail.com",
    description="A simple yet extensible cross-platform service manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xz-dev/juststart",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "juststart = juststart.__main__:run",
            "jst = juststart.__main__:run",
        ],
    },
    install_requires=[],
)
