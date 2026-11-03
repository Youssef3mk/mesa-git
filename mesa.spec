# mesa.spec
%global source_date_epoch_from_changelog 0
%global with_hardware 1

# Hardware Driver Flags (Only requested drivers enabled)
%global with_i915       1
%global with_nvk        1
%global with_opencl     1
%global with_va         1

# Disabled unwanted drivers & features
%global with_crocus     0
%global with_iris       0
%global with_radeonsi   0
%global with_r300       0
%global with_r600       0
%global with_vmware     0
%global with_d3d12      0
%global with_vulkan_hw  0
%global with_intel_clc  0
%global with_intel_vk_rt 0

%if !0%{?rhel}
%global with_libunwind  1
%global with_lmsensors  1
%endif

%ifarch %{valgrind_arches}
%bcond_without valgrind
%else
%bcond_with valgrind
%endif

# Set vulkan drivers to NVK (nouveau) only + swrast
%global vulkan_drivers swrast,nouveau

## additional functionality (Vulkan Overlay Disabled Completely)
%global with_vulkan_overlay 0
%global with_gallium_extra_hud 1
%global with_vulkan_beta 1
%global with_gpuvis 0
%global with_spirv_to_dxil 0
%global with_mesa_tools 0
%global with_xlib_lease 1

%global commit 1d4b5ef4a5562b6e2dba2cb5aacd60787979ba86
%global shortcommit 1d4b5ef

Name:           mesa
Summary:        Mesa graphics libraries (Custom build: i915, nvk, rusticl, nouveau, va)
Version:        28.10
Release:        0.26111.git%{shortcommit}%{?dist}

License:        MIT AND BSD-3-Clause AND SGI-B-2.0
URL:            http://www.mesa3d.org

Source0:        https://gitlab.freedesktop.org/mesa/mesa/-/archive/%{commit}.tar.gz#/mesa-%{commit}.tar.gz
Patch0:         sum.patch
Patch1:         vk.patch

BuildRequires:  meson >= 1.7.0
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  gettext
BuildRequires:  libdisplay-info-devel

%if 0%{?with_hardware}
BuildRequires:  kernel-headers
%endif
BuildRequires:  pkgconfig(libdrm) >= 2.4.97
%if 0%{?with_libunwind}
BuildRequires:  pkgconfig(libunwind)
%endif
BuildRequires:  pkgconfig(expat)
BuildRequires:  pkgconfig(zlib) >= 1.2.3
BuildRequires:  pkgconfig(libzstd)
BuildRequires:  pkgconfig(wayland-scanner)
BuildRequires:  pkgconfig(wayland-protocols) >= 1.8
BuildRequires:  pkgconfig(wayland-client) >= 1.11
BuildRequires:  pkgconfig(wayland-server) >= 1.11
BuildRequires:  pkgconfig(wayland-egl-backend) >= 3
BuildRequires:  pkgconfig(x11)
BuildRequires:  pkgconfig(xext)
BuildRequires:  pkgconfig(xdamage) >= 1.1
BuildRequires:  pkgconfig(xfixes)
BuildRequires:  pkgconfig(xcb-glx) >= 1.8.1
BuildRequires:  pkgconfig(xxf86vm)
BuildRequires:  pkgconfig(xcb)
BuildRequires:  pkgconfig(x11-xcb)
BuildRequires:  pkgconfig(xcb-dri2) >= 1.8
BuildRequires:  pkgconfig(xcb-dri3)
BuildRequires:  pkgconfig(xcb-present)
BuildRequires:  pkgconfig(xcb-sync)
BuildRequires:  pkgconfig(xshmfence) >= 1.1
BuildRequires:  pkgconfig(dri2proto) >= 2.8
BuildRequires:  pkgconfig(glproto) >= 1.4.14
BuildRequires:  pkgconfig(xcb-xfixes)
BuildRequires:  pkgconfig(xcb-randr)
BuildRequires:  pkgconfig(glfw3)
BuildRequires:  pkgconfig(xrandr) >= 1.3
BuildRequires:  bison
BuildRequires:  flex
%if 0%{?with_lmsensors}
BuildRequires:  lm_sensors-devel
%endif

%if 0%{?with_va}
BuildRequires:  pkgconfig(libva) >= 0.38.0
%endif
BuildRequires:  pkgconfig(libelf)
BuildRequires:  pkgconfig(libglvnd) >= 1.3.2
BuildRequires:  llvm-devel >= 7.0.0

# Dependencies for OpenCL (Rusticl) & NVK (Rust-based driver)
%if 0%{?with_opencl} || 0%{?with_nvk}
BuildRequires:  clang-devel
BuildRequires:  pkgconfig(libclc)
BuildRequires:  pkgconfig(SPIRV-Tools)
BuildRequires:  pkgconfig(LLVMSPIRVLib)
BuildRequires:  bindgen
BuildRequires:  rust-packaging
BuildRequires:  rustfmt
BuildRequires:  cbindgen
BuildRequires:  (crate(paste/default) >= 1.0.14 with crate(paste/default) < 2)
BuildRequires:  (crate(proc-macro2) >= 1.0.56 with crate(proc-macro2) < 2)
BuildRequires:  (crate(quote) >= 1.0.25 with crate(quote) < 2)
BuildRequires:  (crate(syn/clone-impls) >= 2.0.15 with crate(syn/clone-impls) < 3)
BuildRequires:  (crate(unicode-ident) >= 1.0.6 with crate(unicode-ident) < 2)
BuildRequires:  (crate(rustc-hash) >= 2.0.0 with crate(rustc-hash) < 3)
%endif

%if %{with valgrind}
BuildRequires:  pkgconfig(valgrind)
%endif
BuildRequires:  python3-devel
BuildRequires:  python3-mako
BuildRequires:  python3-pycparser
BuildRequires:  python3-pyyaml
BuildRequires:  vulkan-headers
BuildRequires:  glslang
BuildRequires:  pkgconfig(libpng)
BuildRequires:  pkgconfig(epoxy)
BuildRequires:  pkgconfig(gtk+-3.0)
BuildRequires:  cmake git

%description
%{summary}.

%package filesystem
Summary:        Mesa driver filesystem
Provides:       mesa-dri-filesystem = %{?epoch:%{epoch}:}%{version}-%{release}

%description filesystem
%{summary}.

%package libGL
Summary:        Mesa libGL runtime libraries
Requires:       libglvnd-glx%{?_isa} >= 1:1.3.2
Recommends:     %{name}-dri-drivers%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description libGL
%{summary}.

%package libGL-devel
Summary:        Mesa libGL development package
Requires:       %{name}-libGL%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires:       libglvnd-devel%{?_isa} >= 1:1.3.2
Provides:       libGL-devel
Provides:       libGL-devel%{?_isa}

%description libGL-devel
%{summary}.

%package libEGL
Summary:        Mesa libEGL runtime libraries
Requires:       libglvnd-egl%{?_isa} >= 1:1.3.2
Requires:       %{name}-libgbm%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description libEGL
%{summary}.

%package libEGL-devel
Summary:        Mesa libEGL development package
Requires:       %{name}-libEGL%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires:       libglvnd-devel%{?_isa} >= 1:1.3.2
Provides:       libEGL-devel
Provides:       libEGL-devel%{?_isa}

%description libEGL-devel
%{summary}.

%package dri-drivers
Summary:        Mesa-based DRI drivers (i915, nouveau)
Requires:       %{name}-filesystem%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
%if 0%{?with_va}
Recommends:     %{name}-va-drivers%{?_isa}
%endif

%description dri-drivers
%{summary}.

%if 0%{?with_va}
%package va-drivers
Summary:        Mesa-based VA-API video acceleration drivers
Requires:       %{name}-filesystem%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description va-drivers
%{summary}.
%endif

%package libgbm
Summary:        Mesa gbm runtime library
Provides:       libgbm
Provides:       libgbm%{?_isa}

%description libgbm
%{summary}.

%package libgbm-devel
Summary:        Mesa libgbm development package
Requires:       %{name}-libgbm%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Provides:       libgbm-devel
Provides:       libgbm-devel%{?_isa}

%description libgbm-devel
%{summary}.

%if 0%{?with_opencl}
%package libOpenCL
Summary:        Mesa Rusticl OpenCL runtime library
Requires:       ocl-icd%{?_isa}
Requires:       libclc%{?_isa}
Requires:       %{name}-libgbm%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires:       opencl-filesystem

%description libOpenCL
%{summary}.

%package libOpenCL-devel
Summary:        Mesa OpenCL development package
Requires:       %{name}-libOpenCL%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description libOpenCL-devel
%{summary}.
%endif

%package vulkan-drivers
Summary:        Mesa NVK Vulkan driver
Requires:       vulkan%{_isa}
Requires:       %{name}-filesystem%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description vulkan-drivers
NVIDIA NVK Vulkan driver and software rast driver.

%prep
%autosetup -n mesa-%{commit} -p1

%build
export RUSTFLAGS="%build_rustflags"

%if 0%{?with_nvk}
export MESON_PACKAGE_CACHE_DIR="%{cargo_registry}/"

%define inst_crate_nameversion() %( \
  found_dir=$(find %{cargo_registry} -maxdepth 1 -type d -name '%{1}-*' 2>/dev/null | head -n1); \
  if [ -n "$found_dir" ]; then basename "$found_dir"; fi \
)

%define rewrite_wrap_file() \
  wrapfile=$(find subprojects -maxdepth 1 -name '%{1}*.wrap' | head -n1) && \
  if [ -z "$wrapfile" ]; then \
    echo "ERROR: .wrap file not found for crate %{1}" >&2; exit 1; \
  fi && \
  crate_dir="%{expand:%%inst_crate_nameversion %{1}}" && \
  if [ -z "$crate_dir" ]; then \
    echo "ERROR: Crate directory not found in %{cargo_registry} for %{1}" >&2; exit 1; \
  fi && \
  echo "→ Rewriting $wrapfile to use directory = $crate_dir" && \
  sed -i -e '/^source_/d' -e "s|^directory = .*|directory = ${crate_dir}|" "$wrapfile"

%rewrite_wrap_file paste
%rewrite_wrap_file proc-macro2
%rewrite_wrap_file quote
%rewrite_wrap_file syn
%rewrite_wrap_file unicode-ident
%rewrite_wrap_file rustc-hash
%endif

%define _lto_cflags %{nil}

%meson \
  -Dplatforms=x11,wayland \
  -Dgallium-drivers=softpipe,llvmpipe,i915,nouveau,zink \
  -Dgallium-d3d12-video=disabled \
  --wrap-mode=default \
  -Dandroid-libbacktrace=disabled \
  -Dgallium-d3d12-graphics=disabled \
  -Dgallium-va=%{?with_va:enabled}%{!?with_va:disabled} \
  -Dgallium-rusticl=%{?with_opencl:true}%{!?with_opencl:false} \
  -Dgallium-mediafoundation=disabled \
  -Dgallium-extra-hud=%{?with_gallium_extra_hud:true}%{!?with_gallium_extra_hud:false} \
  -Dvulkan-drivers=%{vulkan_drivers} \
  -Dvulkan-layers=device-select \
  -Dvulkan-beta=%{?with_vulkan_beta:true}%{!?with_vulkan_beta:false} \
  -Dxlib-lease=%{?with_xlib_lease:enabled}%{!?with_xlib_lease:disabled} \
  -Dgles1=enabled \
  -Dgles2=enabled \
  -Dopengl=true \
  -Dgbm=enabled \
  -Dglx=dri \
  -Degl=enabled \
  -Dglvnd=enabled \
  -Dintel-rt=disabled \
  -Dmicrosoft-clc=disabled \
  -Dllvm=enabled \
  -Dshared-llvm=enabled \
  -Dvalgrind=%{?with_valgrind:enabled}%{!?with_valgrind:disabled} \
  -Dbuild-tests=false \
  -Dvideo-codecs=all \
%if !0%{?with_libunwind}
  -Dlibunwind=disabled \
%endif
%if !0%{?with_lmsensors}
  -Dlmsensors=disabled \
%endif
  %{nil}

%meson_build

%install
%meson_install

rm -vf %{buildroot}%{_libdir}/libGLX_mesa.so
rm -vf %{buildroot}%{_libdir}/libEGL_mesa.so
rm -vf %{buildroot}%{_libdir}/libGLES*

ln -s libGLX_mesa.so.0 %{buildroot}%{_libdir}/libGLX_system.so.0

%files filesystem
%dir %{_libdir}/dri
%dir %{_datadir}/drirc.d
%{_datadir}/drirc.d/*.conf

%files libGL
%{_libdir}/libGLX_mesa.so.0*
%{_libdir}/libGLX_system.so.0*

%files libGL-devel
%dir %{_includedir}/GL
%dir %{_includedir}/GL/internal
%{_includedir}/GL/internal/dri_interface.h
%{_libdir}/pkgconfig/dri.pc

%files libEGL
%{_datadir}/glvnd/egl_vendor.d/50_mesa.json
%{_libdir}/libEGL_mesa.so.0*

%files libEGL-devel
%dir %{_includedir}/EGL
%{_includedir}/EGL/eglext_angle.h
%{_includedir}/EGL/eglmesaext.h

%files libgbm
%{_libdir}/libgbm.so.1
%{_libdir}/libgbm.so.1.*

%files libgbm-devel
%{_libdir}/libgbm.so
%{_includedir}/gbm.h
%{_includedir}/gbm_backend_abi.h
%{_libdir}/pkgconfig/gbm.pc

%if 0%{?with_opencl}
%files libOpenCL
%{_libdir}/libRusticlOpenCL.so.*
%{_sysconfdir}/OpenCL/vendors/rusticl.icd

%files libOpenCL-devel
%{_libdir}/libRusticlOpenCL.so
%endif

%files dri-drivers
%{_libdir}/libgallium-*.so
%{_libdir}/dri/libdril_dri.so
%{_libdir}/gbm/dri_gbm.so
%{_libdir}/dri/kms_swrast_dri.so
%{_libdir}/dri/swrast_dri.so
%{_libdir}/dri/i915_dri.so
%{_libdir}/dri/nouveau_dri.so
%{_libdir}/dri/zink_dri.so

%if 0%{?with_va}
%files va-drivers
%{_libdir}/dri/nouveau_drv_video.so
%endif

%files vulkan-drivers
%{_libdir}/libvulkan_lvp.so
%{_datadir}/vulkan/icd.d/lvp_icd.*.json
%{_libdir}/libvulkan_nouveau.so
%{_datadir}/vulkan/icd.d/nouveau_icd.*.json
%{_libdir}/libVkLayer_MESA_device_select.so
%{_datadir}/vulkan/implicit_layer.d/VkLayer_MESA_device_select.json
