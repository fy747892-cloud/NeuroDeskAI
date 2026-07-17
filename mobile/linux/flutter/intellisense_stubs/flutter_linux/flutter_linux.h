#ifndef FLUTTER_LINUX_INTELLISENSE_STUB_H_
#define FLUTTER_LINUX_INTELLISENSE_STUB_H_

typedef void GObject;
typedef void GObjectClass;
typedef unsigned long GType;

typedef struct _FlPluginRegistry FlPluginRegistry;
typedef struct _FlPluginRegistrar FlPluginRegistrar;

#ifndef G_BEGIN_DECLS
#define G_BEGIN_DECLS
#endif

#ifndef G_END_DECLS
#define G_END_DECLS
#endif

#ifndef G_DECLARE_FINAL_TYPE
#define G_DECLARE_FINAL_TYPE(TypeName, type_name, MODULE, OBJ_NAME, ParentName) \
  typedef struct _##TypeName TypeName;                                          \
  typedef struct _##TypeName##Class TypeName##Class;
#endif

#ifndef g_autoptr
#define g_autoptr(TypeName) TypeName*
#endif

FlPluginRegistrar* fl_plugin_registry_get_registrar_for_plugin(
    FlPluginRegistry* registry,
    const char* plugin_name);

#endif
