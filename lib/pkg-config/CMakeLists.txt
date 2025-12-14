cmake_minimum_required(VERSION 3.16)

project(pkg_config C)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

# --- Sources ---
set(PKG_CONFIG_SRC
    glib/glib-compat.c
    glib/gmessages.c
    glib/gstrfuncs.c
    glib/glist.c
    glib/gslist.c
    glib/gstring.c
    glib/gutils.c
    glib/gprintf.c
    glib/gmem.c
    glib/gatomic.c
    glib/gthread.c
    glib/gthread-posix.c
    glib/gerror.c
    glib/giochannel.c
    glib/gkeyfile.c
    glib/goption.c
    glib/gregex.c
    glib/gspawn.c
    glib/gstrtod.c
    glib/gtimezone.c
    glib/guniprop.c
    glib/gutf8.c

    libpkgconf/argvsplit.c
    libpkgconf/audit.c
    libpkgconf/cache.c
    libpkgconf/client.c
    libpkgconf/dependency.c
    libpkgconf/fragment.c
    libpkgconf/path.c
    libpkgconf/pkg.c
    libpkgconf/pkg-config.c
    libpkgconf/parser.c
    libpkgconf/queue.c
    libpkgconf/tuple.c
    libpkgconf/utils.c

    main.c
)

# --- Executable ---
add_executable(pkg-config ${PKG_CONFIG_SRC})

# --- Include paths ---
target_include_directories(pkg-config PRIVATE
    .
    glib
    libpkgconf
)

# --- Platform specifics ---
if (WIN32)
    target_compile_definitions(pkg-config PRIVATE
        _CRT_SECURE_NO_WARNINGS
        G_OS_WIN32
        WIN32_LEAN_AND_MEAN
    )
else()
    target_compile_definitions(pkg-config PRIVATE
        G_OS_UNIX
    )
endif()

# --- Warnings ---
if (MSVC)
    target_compile_options(pkg-config PRIVATE /W3)
else()
    target_compile_options(pkg-config PRIVATE -Wall -Wextra)
endif()
