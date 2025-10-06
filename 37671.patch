From cfeabbcc5286ff3294b4e594e5abd6de3ed8754b Mon Sep 17 00:00:00 2001
From: Mel Henning <mhenning@darkrefraction.com>
Date: Wed, 6 Aug 2025 18:42:19 -0400
Subject: [PATCH 01/15] nvk: Only run one INVALIDATE_SHADER_CACHES

This is presumably the same cache across compute and 3d, so we only need
to run one of these, not two.
---
 src/nouveau/vulkan/nvk_cmd_buffer.c | 14 ++++++++------
 1 file changed, 8 insertions(+), 6 deletions(-)

diff --git a/src/nouveau/vulkan/nvk_cmd_buffer.c b/src/nouveau/vulkan/nvk_cmd_buffer.c
index c0d08dc45105f..f9c0d885c6423 100644
--- a/src/nouveau/vulkan/nvk_cmd_buffer.c
+++ b/src/nouveau/vulkan/nvk_cmd_buffer.c
@@ -525,6 +525,10 @@ nvk_cmd_flush_wait_dep(struct nvk_cmd_buffer *cmd,
                        const VkDependencyInfo *dep,
                        bool wait)
 {
+   VkQueueFlags queue_flags = nvk_cmd_buffer_queue_flags(cmd);
+   enum nvkmd_engines engines =
+      nvk_queue_engines_from_queue_flags(queue_flags);
+
    enum nvk_barrier barriers = 0;
 
    for (uint32_t i = 0; i < dep->memoryBarrierCount; i++) {
@@ -548,18 +552,16 @@ nvk_cmd_flush_wait_dep(struct nvk_cmd_buffer *cmd,
    if (!barriers)
       return;
 
-   struct nv_push *p = nvk_cmd_buffer_push(cmd, 4);
+   struct nv_push *p = nvk_cmd_buffer_push(cmd, 2);
 
    if (barriers & NVK_BARRIER_FLUSH_SHADER_DATA) {
-      assert(barriers & (NVK_BARRIER_RENDER_WFI | NVK_BARRIER_COMPUTE_WFI));
-      if (barriers & NVK_BARRIER_RENDER_WFI) {
+      /* This is also implicitly a WFI */
+      if (engines & NVKMD_ENGINE_3D) {
          P_IMMD(p, NVA097, INVALIDATE_SHADER_CACHES, {
             .data = DATA_TRUE,
             .flush_data = FLUSH_DATA_TRUE,
          });
-      }
-
-      if (barriers & NVK_BARRIER_COMPUTE_WFI) {
+      } else {
          P_IMMD(p, NVA0C0, INVALIDATE_SHADER_CACHES, {
             .data = DATA_TRUE,
             .flush_data = FLUSH_DATA_TRUE,
-- 
GitLab


From 651ebd831ef034e1f50b3fa791433b22caebd508 Mon Sep 17 00:00:00 2001
From: Mel Henning <mhenning@darkrefraction.com>
Date: Wed, 1 Oct 2025 19:11:00 -0400
Subject: [PATCH 02/15] nvk: Combine BARRIER_{COMPUTE,RENDER}_WFI

When we want to WFI, we only need to do so on a single channel. The
others will implicitly get a WFI from the channel switch.
---
 src/nouveau/vulkan/nvk_cmd_buffer.c | 24 ++++++++++++------------
 1 file changed, 12 insertions(+), 12 deletions(-)

diff --git a/src/nouveau/vulkan/nvk_cmd_buffer.c b/src/nouveau/vulkan/nvk_cmd_buffer.c
index f9c0d885c6423..5c88d55df4636 100644
--- a/src/nouveau/vulkan/nvk_cmd_buffer.c
+++ b/src/nouveau/vulkan/nvk_cmd_buffer.c
@@ -434,8 +434,7 @@ nvk_CmdExecuteCommands(VkCommandBuffer commandBuffer,
 }
 
 enum nvk_barrier {
-   NVK_BARRIER_RENDER_WFI              = 1 << 0,
-   NVK_BARRIER_COMPUTE_WFI             = 1 << 1,
+   NVK_BARRIER_WFI                     = 1 << 0,
    NVK_BARRIER_FLUSH_SHADER_DATA       = 1 << 2,
    NVK_BARRIER_INVALIDATE_SHADER_DATA  = 1 << 3,
    NVK_BARRIER_INVALIDATE_TEX_DATA     = 1 << 4,
@@ -457,26 +456,26 @@ nvk_barrier_flushes_waits(VkPipelineStageFlags2 stages,
       barriers |= NVK_BARRIER_FLUSH_SHADER_DATA;
 
       if (vk_pipeline_stage_flags2_has_graphics_shader(stages))
-         barriers |= NVK_BARRIER_RENDER_WFI;
+         barriers |= NVK_BARRIER_WFI;
 
       if (vk_pipeline_stage_flags2_has_compute_shader(stages))
-         barriers |= NVK_BARRIER_COMPUTE_WFI;
+         barriers |= NVK_BARRIER_WFI;
    }
 
    if (access & (VK_ACCESS_2_COLOR_ATTACHMENT_WRITE_BIT |
                  VK_ACCESS_2_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT |
                  VK_ACCESS_2_TRANSFORM_FEEDBACK_WRITE_BIT_EXT))
-      barriers |= NVK_BARRIER_RENDER_WFI;
+      barriers |= NVK_BARRIER_WFI;
 
    if ((access & VK_ACCESS_2_TRANSFER_WRITE_BIT) &&
        (stages & (VK_PIPELINE_STAGE_2_RESOLVE_BIT |
                   VK_PIPELINE_STAGE_2_BLIT_BIT |
                   VK_PIPELINE_STAGE_2_CLEAR_BIT)))
-      barriers |= NVK_BARRIER_RENDER_WFI;
+      barriers |= NVK_BARRIER_WFI;
 
    if (access & VK_ACCESS_2_COMMAND_PREPROCESS_WRITE_BIT_EXT)
       barriers |= NVK_BARRIER_FLUSH_SHADER_DATA |
-                  NVK_BARRIER_COMPUTE_WFI;
+                  NVK_BARRIER_WFI;
 
    return barriers;
 }
@@ -567,13 +566,14 @@ nvk_cmd_flush_wait_dep(struct nvk_cmd_buffer *cmd,
             .flush_data = FLUSH_DATA_TRUE,
          });
       }
-   } else if (barriers & NVK_BARRIER_RENDER_WFI) {
-      /* If this comes from a vkCmdSetEvent, we don't need to wait */
+   } else if (barriers & NVK_BARRIER_WFI) {
+      /* If this comes from a vkCmdSetEvent, we don't need to wait
+       *
+       * We only need to WFI on a single channel. The others will implicitly get
+       * a WFI from the channel switch.
+       */
       if (wait)
          P_IMMD(p, NVA097, WAIT_FOR_IDLE, 0);
-   } else {
-      /* Compute WFI only happens when shader data is flushed */
-      assert(!(barriers & NVK_BARRIER_COMPUTE_WFI));
    }
 }
 
-- 
GitLab


From 069e44e902fe75329ecb1393b9b3128753e3e394 Mon Sep 17 00:00:00 2001
From: Mel Henning <mhenning@darkrefraction.com>
Date: Wed, 1 Oct 2025 19:15:30 -0400
Subject: [PATCH 03/15] nvk: Renumber enum nvk_barrier

---
 src/nouveau/vulkan/nvk_cmd_buffer.c | 12 ++++++------
 1 file changed, 6 insertions(+), 6 deletions(-)

diff --git a/src/nouveau/vulkan/nvk_cmd_buffer.c b/src/nouveau/vulkan/nvk_cmd_buffer.c
index 5c88d55df4636..59620b5a2ddff 100644
--- a/src/nouveau/vulkan/nvk_cmd_buffer.c
+++ b/src/nouveau/vulkan/nvk_cmd_buffer.c
@@ -435,12 +435,12 @@ nvk_CmdExecuteCommands(VkCommandBuffer commandBuffer,
 
 enum nvk_barrier {
    NVK_BARRIER_WFI                     = 1 << 0,
-   NVK_BARRIER_FLUSH_SHADER_DATA       = 1 << 2,
-   NVK_BARRIER_INVALIDATE_SHADER_DATA  = 1 << 3,
-   NVK_BARRIER_INVALIDATE_TEX_DATA     = 1 << 4,
-   NVK_BARRIER_INVALIDATE_CONSTANT     = 1 << 5,
-   NVK_BARRIER_INVALIDATE_MME_DATA     = 1 << 6,
-   NVK_BARRIER_INVALIDATE_QMD_DATA     = 1 << 7,
+   NVK_BARRIER_FLUSH_SHADER_DATA       = 1 << 1,
+   NVK_BARRIER_INVALIDATE_SHADER_DATA  = 1 << 2,
+   NVK_BARRIER_INVALIDATE_TEX_DATA     = 1 << 3,
+   NVK_BARRIER_INVALIDATE_CONSTANT     = 1 << 4,
+   NVK_BARRIER_INVALIDATE_MME_DATA     = 1 << 5,
+   NVK_BARRIER_INVALIDATE_QMD_DATA     = 1 << 6,
 };
 
 static enum nvk_barrier
-- 
GitLab


From 5d1368c2db2fd7d3cf2d32edf4a1073bca1cb8c0 Mon Sep 17 00:00:00 2001
From: Mel Henning <mhenning@darkrefraction.com>
Date: Tue, 16 Sep 2025 19:37:37 -0400
Subject: [PATCH 04/15] nvk: Fix execution deps in pipeline barriers

We were under-synchronizing before. In particular, `stages` form
execution barriers even in the absence of a memory barrier in the
`access` flags.

The particular issue that prompted this was one where we weren't waiting
on a pipeline barrier in Baldur's Gate 3 with:

    srcStageMask == VK_PIPELINE_STAGE_2_FRAGMENT_SHADER_BIT &&
    srcAccessMask == VK_ACCESS_2_SHADER_READ_BIT &&
    dstStageMask == (VK_PIPELINE_STAGE_2_EARLY_FRAGMENT_TESTS_BIT |
                     VK_PIPELINE_STAGE_2_LATE_FRAGMENT_TESTS_BIT) &&
    dstAccessMask == (VK_ACCESS_2_DEPTH_STENCIL_ATTACHMENT_READ_BIT |
                      VK_ACCESS_2_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT)

Based on the spec and discussion in
https://github.com/KhronosGroup/Vulkan-Docs/issues/131 the read bit in
srcAccessMask doesn't really matter here - what matters is that there's
an execution barrier on the fragment stage which needs to prevent the
fragment shader exection from overlapping with the later call's
fragment tests (which write to the depth attachment).

Closes: https://gitlab.freedesktop.org/mesa/mesa/-/issues/13909
---
 src/nouveau/vulkan/nvk_cmd_buffer.c | 5 +++++
 1 file changed, 5 insertions(+)

diff --git a/src/nouveau/vulkan/nvk_cmd_buffer.c b/src/nouveau/vulkan/nvk_cmd_buffer.c
index 59620b5a2ddff..3fec5b944d3a9 100644
--- a/src/nouveau/vulkan/nvk_cmd_buffer.c
+++ b/src/nouveau/vulkan/nvk_cmd_buffer.c
@@ -22,6 +22,7 @@
 #include "clb097.h"
 #include "clcb97.h"
 #include "nv_push_cl906f.h"
+#include "nv_push_cla16f.h"
 #include "nv_push_cl9097.h"
 #include "nv_push_cl90b5.h"
 #include "nv_push_cla097.h"
@@ -452,6 +453,10 @@ nvk_barrier_flushes_waits(VkPipelineStageFlags2 stages,
 
    enum nvk_barrier barriers = 0;
 
+   if (stages &
+       vk_expand_pipeline_stage_flags2(VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT))
+      barriers |= NVK_BARRIER_WFI;
+
    if (access & VK_ACCESS_2_SHADER_STORAGE_WRITE_BIT) {
       barriers |= NVK_BARRIER_FLUSH_SHADER_DATA;
 
-- 
GitLab


From 8f2b2fe3bd0ac5b9d9a59c6f69fa39f2b16bd6eb Mon Sep 17 00:00:00 2001
From: Mel Henning <mhenning@darkrefraction.com>
Date: Wed, 24 Sep 2025 14:22:37 -0400
Subject: [PATCH 05/15] nvk/cmd_buffer: Remove redundant tests for access

In each of these cases, the spec mandates that apps pair a memory barrier
specified with access with a relevant exec barrrier specified by stages.
We therefore don't need to wfi based on access - the tests on stage are
sufficient.

Acked-by: Mary Guillemard <mary@mary.zone>
---
 src/nouveau/vulkan/nvk_cmd_buffer.c | 23 ++---------------------
 1 file changed, 2 insertions(+), 21 deletions(-)

diff --git a/src/nouveau/vulkan/nvk_cmd_buffer.c b/src/nouveau/vulkan/nvk_cmd_buffer.c
index 3fec5b944d3a9..4e224dff6177b 100644
--- a/src/nouveau/vulkan/nvk_cmd_buffer.c
+++ b/src/nouveau/vulkan/nvk_cmd_buffer.c
@@ -457,30 +457,11 @@ nvk_barrier_flushes_waits(VkPipelineStageFlags2 stages,
        vk_expand_pipeline_stage_flags2(VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT))
       barriers |= NVK_BARRIER_WFI;
 
-   if (access & VK_ACCESS_2_SHADER_STORAGE_WRITE_BIT) {
+   if (access & VK_ACCESS_2_SHADER_STORAGE_WRITE_BIT)
       barriers |= NVK_BARRIER_FLUSH_SHADER_DATA;
 
-      if (vk_pipeline_stage_flags2_has_graphics_shader(stages))
-         barriers |= NVK_BARRIER_WFI;
-
-      if (vk_pipeline_stage_flags2_has_compute_shader(stages))
-         barriers |= NVK_BARRIER_WFI;
-   }
-
-   if (access & (VK_ACCESS_2_COLOR_ATTACHMENT_WRITE_BIT |
-                 VK_ACCESS_2_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT |
-                 VK_ACCESS_2_TRANSFORM_FEEDBACK_WRITE_BIT_EXT))
-      barriers |= NVK_BARRIER_WFI;
-
-   if ((access & VK_ACCESS_2_TRANSFER_WRITE_BIT) &&
-       (stages & (VK_PIPELINE_STAGE_2_RESOLVE_BIT |
-                  VK_PIPELINE_STAGE_2_BLIT_BIT |
-                  VK_PIPELINE_STAGE_2_CLEAR_BIT)))
-      barriers |= NVK_BARRIER_WFI;
-
    if (access & VK_ACCESS_2_COMMAND_PREPROCESS_WRITE_BIT_EXT)
-      barriers |= NVK_BARRIER_FLUSH_SHADER_DATA |
-                  NVK_BARRIER_WFI;
+      barriers |= NVK_BARRIER_FLUSH_SHADER_DATA;
 
    return barriers;
 }
-- 
GitLab


From 625c2b38e2aed9895d68eed58f9f09dc472510e8 Mon Sep 17 00:00:00 2001
From: Mel Henning <mhenning@darkrefraction.com>
Date: Thu, 2 Oct 2025 12:46:05 -0400
Subject: [PATCH 06/15] vulkan: Drop vk_pipeline_stage_flags2_has_*_shader

These are no longer used anywhere. Moreover, it's not clear that they
can be used for a correct implementation of pipeline barriers since a
correct implementation cannot ignore execution deps in non-shader
stages.
---
 src/vulkan/runtime/vk_synchronization.h | 25 -------------------------
 1 file changed, 25 deletions(-)

diff --git a/src/vulkan/runtime/vk_synchronization.h b/src/vulkan/runtime/vk_synchronization.h
index 0ffbc2d3b202d..c7ce69b7c54d1 100644
--- a/src/vulkan/runtime/vk_synchronization.h
+++ b/src/vulkan/runtime/vk_synchronization.h
@@ -31,31 +31,6 @@
 extern "C" {
 #endif
 
-static inline bool
-vk_pipeline_stage_flags2_has_graphics_shader(VkPipelineStageFlags2 stages)
-{
-   return stages & (VK_PIPELINE_STAGE_2_TOP_OF_PIPE_BIT |
-                    VK_PIPELINE_STAGE_2_VERTEX_SHADER_BIT |
-                    VK_PIPELINE_STAGE_2_TESSELLATION_CONTROL_SHADER_BIT |
-                    VK_PIPELINE_STAGE_2_TESSELLATION_EVALUATION_SHADER_BIT |
-                    VK_PIPELINE_STAGE_2_GEOMETRY_SHADER_BIT |
-                    VK_PIPELINE_STAGE_2_FRAGMENT_SHADER_BIT |
-                    VK_PIPELINE_STAGE_2_BOTTOM_OF_PIPE_BIT |
-                    VK_PIPELINE_STAGE_2_ALL_GRAPHICS_BIT |
-                    VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT |
-                    VK_PIPELINE_STAGE_2_TASK_SHADER_BIT_EXT |
-                    VK_PIPELINE_STAGE_2_MESH_SHADER_BIT_EXT);
-}
-
-static inline bool
-vk_pipeline_stage_flags2_has_compute_shader(VkPipelineStageFlags2 stages)
-{
-   return stages & (VK_PIPELINE_STAGE_2_TOP_OF_PIPE_BIT |
-                    VK_PIPELINE_STAGE_2_COMPUTE_SHADER_BIT |
-                    VK_PIPELINE_STAGE_2_BOTTOM_OF_PIPE_BIT |
-                    VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT);
-}
-
 /** Expands pipeline stage group flags
  *
  * Some stages like VK_PIPELINE_SHADER_STAGE_2_ALL_GRAPHICS_BIT represent more
-- 
GitLab


From cc283926b6e4c05618a703222a222373654c47c6 Mon Sep 17 00:00:00 2001
From: Mohamed Ahmed <mohamedahmedegypt2001@gmail.com>
Date: Wed, 27 Aug 2025 01:24:08 +0300
Subject: [PATCH 07/15] nouveau/headers: Add AMPERE_B compute subchannel
 definition

Reviewed-by: Karol Herbst <kherbst@redhat.com>
Reviewed-by: Faith Ekstrand <faith.ekstrand@collabora.com>
---
 src/nouveau/headers/nv_push.h | 1 +
 1 file changed, 1 insertion(+)

diff --git a/src/nouveau/headers/nv_push.h b/src/nouveau/headers/nv_push.h
index d884086cc76b8..bfb8536beeed9 100644
--- a/src/nouveau/headers/nv_push.h
+++ b/src/nouveau/headers/nv_push.h
@@ -81,6 +81,7 @@ void vk_push_print(FILE *fp, const struct nv_push *push,
 #define SUBC_NVC0C0 1
 #define SUBC_NVC3C0 1
 #define SUBC_NVC6C0 1
+#define SUBC_NVC7C0 1
 
 #define SUBC_NV9039 2
 
-- 
GitLab


From 39a660dcb275fc5ed3fef931ac9563b5f14b9156 Mon Sep 17 00:00:00 2001
From: Faith Ekstrand <faith.ekstrand@collabora.com>
Date: Tue, 23 Sep 2025 10:42:18 -0400
Subject: [PATCH 08/15] nvk: Actually reserve 1/2 for FALCON

In 03f785083f0b ("nvk: Reserve MME scratch area for communicating with
FALCON"), we said we reserved these but actually only reserved 0.  Only
0 is actually used today but if we're going to claim to reserve
registers we should actually do it.
---
 src/nouveau/vulkan/nvk_mme.h | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)

diff --git a/src/nouveau/vulkan/nvk_mme.h b/src/nouveau/vulkan/nvk_mme.h
index 6dde205bd2729..18475ab130b0d 100644
--- a/src/nouveau/vulkan/nvk_mme.h
+++ b/src/nouveau/vulkan/nvk_mme.h
@@ -46,8 +46,8 @@ enum nvk_mme {
 enum nvk_mme_scratch {
    /* These are reserved for communicating with FALCON */
    NVK_MME_SCRATCH_FALCON_0 = 0,
-   NVK_MME_SCRATCH_FALCON_1 = 0,
-   NVK_MME_SCRATCH_FALCON_2 = 0,
+   NVK_MME_SCRATCH_FALCON_1 = 1,
+   NVK_MME_SCRATCH_FALCON_2 = 2,
 
    NVK_MME_SCRATCH_CS_INVOCATIONS_HI,
    NVK_MME_SCRATCH_CS_INVOCATIONS_LO,
-- 
GitLab


From 8ff5400f524f9baca04427eed9854987d2d4ea15 Mon Sep 17 00:00:00 2001
From: Mohamed Ahmed <mohamedahmedegypt2001@gmail.com>
Date: Fri, 19 Sep 2025 01:55:25 +0300
Subject: [PATCH 09/15] nouveau/mme: Add unit tests for sharing between compute
 and 3D scratch registers

Co-developed-by: Mary Guillemard <mary@mary.zone>
Reviewed-by: Karol Herbst <kherbst@redhat.com>
Reviewed-by: Faith Ekstrand <faith.ekstrand@collabora.com>
---
 src/nouveau/headers/class_parser.py           |   1 +
 src/nouveau/mme/tests/mme_runner.cpp          |   7 +
 src/nouveau/mme/tests/mme_runner.h            |  31 +++++
 .../mme/tests/mme_tu104_sim_hw_test.cpp       | 121 ++++++++++++++++++
 src/nouveau/vulkan/nvk_mme.h                  |   8 ++
 5 files changed, 168 insertions(+)

diff --git a/src/nouveau/headers/class_parser.py b/src/nouveau/headers/class_parser.py
index 51a9934063599..9172589ec2593 100644
--- a/src/nouveau/headers/class_parser.py
+++ b/src/nouveau/headers/class_parser.py
@@ -27,6 +27,7 @@ METHOD_ARRAY_SIZES = {
     'SET_COLOR_COMPRESSION'                                 : 8,
     'SET_COLOR_CLEAR_VALUE'                                 : 4,
     'SET_CT_WRITE'                                          : 8,
+    # For compute, this is only 8:
     'SET_MME_SHADOW_SCRATCH'                                : 256,
     'SET_MULTI_VIEW_RENDER_TARGET_ARRAY_INDEX_OFFSET'       : 4,
     'SET_PIPELINE_*'                                        : 6,
diff --git a/src/nouveau/mme/tests/mme_runner.cpp b/src/nouveau/mme/tests/mme_runner.cpp
index b18c21d8c59a9..239589bb25cbc 100644
--- a/src/nouveau/mme/tests/mme_runner.cpp
+++ b/src/nouveau/mme/tests/mme_runner.cpp
@@ -12,6 +12,7 @@
 #include "mme_tu104_sim.h"
 
 #include "nv_push_clc597.h"
+#include "nv_push_cl90c0.h"
 
 #include "nouveau_bo.h"
 #include "nouveau_context.h"
@@ -142,6 +143,12 @@ mme_hw_runner::reset_push()
       .class_id = dev->info.cls_eng3d,
       .engine_id = 0,
    });
+
+   P_MTHD(p, NV90C0, SET_OBJECT);
+   P_NV90C0_SET_OBJECT(p, {
+      .class_id = dev->info.cls_compute,
+      .engine_id = 0,
+   });
 }
 
 void
diff --git a/src/nouveau/mme/tests/mme_runner.h b/src/nouveau/mme/tests/mme_runner.h
index 3a7a8bcad93ca..fa19d57c08524 100644
--- a/src/nouveau/mme/tests/mme_runner.h
+++ b/src/nouveau/mme/tests/mme_runner.h
@@ -13,6 +13,7 @@ struct nouveau_ws_device;
 
 #include "nv_push.h"
 #include "nv_push_cl9097.h"
+#include "nv_push_clc7c0.h"
 
 #define DATA_BO_SIZE 4096
 #define DATA_DWORDS 1024
@@ -133,3 +134,33 @@ mme_store(mme_builder *b, struct mme_value64 addr, mme_value v,
    if (free_reg && v.type == MME_VALUE_TYPE_REG)
       mme_free_reg(b, v);
 }
+
+inline void
+mme_store_compute_imm_addr(mme_builder *b, uint64_t addr, mme_value v,
+                           bool free_reg = false)
+{
+   mme_mthd(b, NVC7C0_SET_REPORT_SEMAPHORE_PAYLOAD_LOWER);
+   mme_emit(b, v);
+   mme_emit(b, mme_imm(0));
+   mme_emit(b, mme_imm(low32(addr)));
+   mme_emit(b, mme_imm(high32(addr)));
+   mme_emit(b, mme_imm(0x8));
+
+   if (free_reg && v.type == MME_VALUE_TYPE_REG)
+      mme_free_reg(b, v);
+}
+
+inline void
+mme_store_compute(mme_builder *b, struct mme_value64 addr, mme_value v,
+                  bool free_reg = false)
+{
+   mme_mthd(b, NVC7C0_SET_REPORT_SEMAPHORE_PAYLOAD_LOWER);
+   mme_emit(b, v);
+   mme_emit(b, mme_imm(0));
+   mme_emit(b, addr.lo);
+   mme_emit(b, addr.hi);
+   mme_emit(b, mme_imm(0x8));
+
+   if (free_reg && v.type == MME_VALUE_TYPE_REG)
+      mme_free_reg(b, v);
+}
\ No newline at end of file
diff --git a/src/nouveau/mme/tests/mme_tu104_sim_hw_test.cpp b/src/nouveau/mme/tests/mme_tu104_sim_hw_test.cpp
index 17da6e5ecd295..d8e0277d2b22a 100644
--- a/src/nouveau/mme/tests/mme_tu104_sim_hw_test.cpp
+++ b/src/nouveau/mme/tests/mme_tu104_sim_hw_test.cpp
@@ -1695,3 +1695,124 @@ TEST_F(mme_tu104_sim_test, scratch_limit)
          ASSERT_EQ(data[j], i + j);
    }
 }
+
+TEST_F(mme_tu104_sim_test, sanity_compute)
+{
+   const uint32_t canary = 0xc0ffee01;
+
+   mme_builder b;
+   mme_builder_init(&b, devinfo);
+
+   mme_store_compute_imm_addr(&b, data_addr, mme_imm(canary));
+   auto macro = mme_builder_finish_vec(&b);
+
+   reset_push();
+   push_macro(0, macro);
+
+   P_1INC(p, NVC7C0, CALL_MME_MACRO(0));
+   P_NVC7C0_CALL_MME_MACRO(p, 0, 0);
+   submit_push();
+
+   ASSERT_EQ(data[0], canary);
+}
+
+TEST_F(mme_tu104_sim_test, scratch_limit_compute)
+{
+   static const uint32_t chunk_size = 4;
+
+   mme_builder b;
+   mme_builder_init(&b, devinfo);
+
+   mme_value start = mme_load(&b);
+   mme_value count = mme_load(&b);
+
+   mme_value i = mme_mov(&b, start);
+   mme_loop(&b, count) {
+      mme_mthd_arr(&b, NVC7C0_SET_MME_SHADOW_SCRATCH(0), i);
+      mme_emit(&b, i);
+      mme_add_to(&b, i, i, mme_imm(1));
+   }
+
+   mme_value j = mme_mov(&b, start);
+   struct mme_value64 addr = mme_mov64(&b, mme_imm64(data_addr));
+
+   mme_loop(&b, count) {
+      mme_value x = mme_state_arr(&b, NVC7C0_SET_MME_SHADOW_SCRATCH(0), j);
+      mme_store_compute(&b, addr, x);
+      mme_add_to(&b, j, j, mme_imm(1));
+      mme_add64_to(&b, addr, addr, mme_imm64(4));
+   }
+
+   auto macro = mme_builder_finish_vec(&b);
+
+   for (uint32_t i = 0; i < 8; i += chunk_size) {
+      reset_push();
+
+      push_macro(0, macro);
+
+      P_1INC(p, NVC7C0, CALL_MME_MACRO(1));
+      P_INLINE_DATA(p, i);
+      P_INLINE_DATA(p, chunk_size);
+
+      submit_push();
+
+      for (uint32_t j = 0; j < chunk_size; j++)
+         ASSERT_EQ(data[j], i + j);
+   }
+}
+
+TEST_F(mme_tu104_sim_test, scratch_share_3d_to_compute)
+{
+   static const uint32_t chunk_size = 4;
+   
+   mme_builder b;
+   mme_builder_init(&b, devinfo);
+
+   mme_value start = mme_load(&b);
+   mme_value count = mme_load(&b);
+   mme_value channel = mme_load(&b);
+
+   mme_if(&b, ieq, channel, mme_zero()) {
+      mme_value i = mme_mov(&b, start);
+      mme_loop(&b, count) {
+         mme_mthd_arr(&b, NVC597_SET_MME_SHADOW_SCRATCH(0), i);
+         mme_emit(&b, i);
+         mme_add_to(&b, i, i, mme_imm(1));
+      }
+   }
+
+   mme_if(&b, ieq, channel, mme_imm(1)) {
+      mme_value i = mme_mov(&b, start);
+      struct mme_value64 addr = mme_mov64(&b, mme_imm64(data_addr));
+
+      mme_loop(&b, count) {
+         mme_value val = mme_state_arr(&b, NVC7C0_SET_MME_SHADOW_SCRATCH(0), i);
+         mme_store_compute(&b, addr, val);
+         mme_add_to(&b, i, i, mme_imm(1));
+         mme_add64_to(&b, addr, addr, mme_imm64(4));
+      }
+   }
+
+   auto macro = mme_builder_finish_vec(&b);
+
+   for (uint32_t i = 0; i < 8; i += chunk_size) {
+      reset_push();
+
+      push_macro(0, macro);
+
+      P_1INC(p, NVC597, CALL_MME_MACRO(0));
+      P_INLINE_DATA(p, i);
+      P_INLINE_DATA(p, chunk_size);
+      P_INLINE_DATA(p, 0);
+
+      P_1INC(p, NVC7C0, CALL_MME_MACRO(0));
+      P_INLINE_DATA(p, i);
+      P_INLINE_DATA(p, chunk_size);
+      P_INLINE_DATA(p, 1);
+
+      submit_push();
+
+      for (uint32_t j = 0; j < chunk_size; j++)
+         ASSERT_EQ(data[j], i + j);
+   }
+}
\ No newline at end of file
diff --git a/src/nouveau/vulkan/nvk_mme.h b/src/nouveau/vulkan/nvk_mme.h
index 18475ab130b0d..06e1d4294ff48 100644
--- a/src/nouveau/vulkan/nvk_mme.h
+++ b/src/nouveau/vulkan/nvk_mme.h
@@ -43,14 +43,22 @@ enum nvk_mme {
    NVK_MME_COUNT,
 };
 
+/*
+ * For the compute MME, as tested in scratch_limit_compute in the unit tests,
+ * we only have 8 registers. Using more than 8 leads to a MMU fault.
+ * Moreover, as tested in scratch_share_3d_to_compute, scratch space isn't
+ * shared between compute and 3D.
+ */
 enum nvk_mme_scratch {
    /* These are reserved for communicating with FALCON */
    NVK_MME_SCRATCH_FALCON_0 = 0,
    NVK_MME_SCRATCH_FALCON_1 = 1,
    NVK_MME_SCRATCH_FALCON_2 = 2,
 
+   /* These need to stay at the top since they get accessed by the compute MME */
    NVK_MME_SCRATCH_CS_INVOCATIONS_HI,
    NVK_MME_SCRATCH_CS_INVOCATIONS_LO,
+
    NVK_MME_SCRATCH_DRAW_BEGIN,
    NVK_MME_SCRATCH_DRAW_COUNT,
    NVK_MME_SCRATCH_DRAW_PAD_DW,
-- 
GitLab


From e52bc6a81d65034f7cfe67a2d53e4b3ace9bc0e7 Mon Sep 17 00:00:00 2001
From: Mohamed Ahmed <mohamedahmedegypt2001@gmail.com>
Date: Wed, 27 Aug 2025 01:31:57 +0300
Subject: [PATCH 10/15] nvk: Use the compute MME for compute dispatch

Switching from compute to 3D and vice versa leads to a long stall which
destroys compute performance. This switches to the compute MME on Ampere
onwards (which was where it was added) for compute dispatches which eliminates
stalling from sub-channel switching in these cases.

Reviewed-by: Karol Herbst <kherbst@redhat.com>
Reviewed-by: Faith Ekstrand <faith.ekstrand@collabora.com>
---
 src/nouveau/vulkan/nvk_cmd_dispatch.c | 11 +++++++++--
 src/nouveau/vulkan/nvk_cmd_indirect.c |  6 +++++-
 src/nouveau/vulkan/nvk_query_pool.c   |  9 ++++++++-
 3 files changed, 22 insertions(+), 4 deletions(-)

diff --git a/src/nouveau/vulkan/nvk_cmd_dispatch.c b/src/nouveau/vulkan/nvk_cmd_dispatch.c
index 2d8c9ced06fbc..e63417389e9fd 100644
--- a/src/nouveau/vulkan/nvk_cmd_dispatch.c
+++ b/src/nouveau/vulkan/nvk_cmd_dispatch.c
@@ -25,6 +25,7 @@
 #include "nv_push_clc3c0.h"
 #include "nv_push_clc597.h"
 #include "nv_push_clc6c0.h"
+#include "nv_push_clc7c0.h"
 #include "nv_push_clc86f.h"
 
 VkResult
@@ -315,7 +316,10 @@ nvk_CmdDispatchBase(VkCommandBuffer commandBuffer,
 
    struct nv_push *p = nvk_cmd_buffer_push(cmd, 7);
 
-   P_1INC(p, NV9097, CALL_MME_MACRO(NVK_MME_ADD_CS_INVOCATIONS));
+   if (nvk_cmd_buffer_compute_cls(cmd) >= AMPERE_COMPUTE_B)
+      P_1INC(p, NVC7C0, CALL_MME_MACRO(NVK_MME_ADD_CS_INVOCATIONS));
+   else
+      P_1INC(p, NV9097, CALL_MME_MACRO(NVK_MME_ADD_CS_INVOCATIONS));
    P_INLINE_DATA(p, cs_invocations >> 32);
    P_INLINE_DATA(p, cs_invocations);
 
@@ -562,7 +566,10 @@ nvk_CmdDispatchIndirect(VkCommandBuffer commandBuffer,
       p = nvk_cmd_buffer_push(cmd, 14);
       if (nvk_cmd_buffer_compute_cls(cmd) < BLACKWELL_COMPUTE_A)
          P_IMMD(p, NVC597, SET_MME_DATA_FIFO_CONFIG, FIFO_SIZE_SIZE_4KB);
-      P_1INC(p, NV9097, CALL_MME_MACRO(NVK_MME_DISPATCH_INDIRECT));
+      if (nvk_cmd_buffer_compute_cls(cmd) >= AMPERE_COMPUTE_B)
+         P_1INC(p, NVC7C0, CALL_MME_MACRO(NVK_MME_DISPATCH_INDIRECT));
+      else
+         P_1INC(p, NV9097, CALL_MME_MACRO(NVK_MME_DISPATCH_INDIRECT));
       P_INLINE_DATA(p, dispatch_addr >> 32);
       P_INLINE_DATA(p, dispatch_addr);
       P_INLINE_DATA(p, root_desc_addr >> 32);
diff --git a/src/nouveau/vulkan/nvk_cmd_indirect.c b/src/nouveau/vulkan/nvk_cmd_indirect.c
index 3af732c84f990..c6d3bd6b0322a 100644
--- a/src/nouveau/vulkan/nvk_cmd_indirect.c
+++ b/src/nouveau/vulkan/nvk_cmd_indirect.c
@@ -20,6 +20,7 @@
 #include "nv_push_cla0c0.h"
 #include "nv_push_clb1c0.h"
 #include "nv_push_clc6c0.h"
+#include "nv_push_clc7c0.h"
 #include "nv_push_clc86f.h"
 
 struct nvk_indirect_commands_layout {
@@ -395,7 +396,10 @@ build_process_cs_cmd_seq(nir_builder *b, struct nvk_nir_push *p,
             /* Now emit commands */
             nir_def *invoc = nir_imul_2x32_64(b, disp_size_x, disp_size_y);
             invoc = nir_imul(b, invoc, nir_u2u64(b, disp_size_z));
-            nvk_nir_P_1INC(b, p, NV9097, CALL_MME_MACRO(NVK_MME_ADD_CS_INVOCATIONS), 2);
+            if (pdev->info.cls_compute >= AMPERE_COMPUTE_B)
+               nvk_nir_P_1INC(b, p, NVC7C0, CALL_MME_MACRO(NVK_MME_ADD_CS_INVOCATIONS), 2);
+            else
+               nvk_nir_P_1INC(b, p, NV9097, CALL_MME_MACRO(NVK_MME_ADD_CS_INVOCATIONS), 2);
             nvk_nir_push_dw(b, p, nir_unpack_64_2x32_split_y(b, invoc));
             nvk_nir_push_dw(b, p, nir_unpack_64_2x32_split_x(b, invoc));
 
diff --git a/src/nouveau/vulkan/nvk_query_pool.c b/src/nouveau/vulkan/nvk_query_pool.c
index 086ca9a26c238..bf6efc3989ae3 100644
--- a/src/nouveau/vulkan/nvk_query_pool.c
+++ b/src/nouveau/vulkan/nvk_query_pool.c
@@ -28,6 +28,7 @@
 #include "nv_push_cl9097.h"
 #include "nv_push_cla0c0.h"
 #include "nv_push_clc597.h"
+#include "nv_push_clc7c0.h"
 
 VKAPI_ATTR VkResult VKAPI_CALL
 nvk_CreateQueryPool(VkDevice device,
@@ -378,6 +379,9 @@ nvk_cmd_begin_end_query(struct nvk_cmd_buffer *cmd,
                         uint32_t query, uint32_t index,
                         bool end)
 {
+   const struct nvk_device *dev = nvk_cmd_buffer_device(cmd);
+   const struct nvk_physical_device *pdev = nvk_device_physical(dev);
+
    uint64_t report_addr = nvk_query_report_addr(pool, query) +
                           end * sizeof(struct nvk_query_report);
 
@@ -417,7 +421,10 @@ nvk_cmd_begin_end_query(struct nvk_cmd_buffer *cmd,
          assert(!(stats_left & (sq->flag - 1)));
 
          if (sq->flag == VK_QUERY_PIPELINE_STATISTIC_COMPUTE_SHADER_INVOCATIONS_BIT) {
-            P_1INC(p, NVC597, CALL_MME_MACRO(NVK_MME_WRITE_CS_INVOCATIONS));
+            if (pdev->info.cls_compute >= AMPERE_COMPUTE_B)
+               P_1INC(p, NVC7C0, CALL_MME_MACRO(NVK_MME_WRITE_CS_INVOCATIONS));
+            else
+               P_1INC(p, NVC597, CALL_MME_MACRO(NVK_MME_WRITE_CS_INVOCATIONS));
             P_INLINE_DATA(p, report_addr >> 32);
             P_INLINE_DATA(p, report_addr);
          } else {
-- 
GitLab


From 906fa846c51e8c0dab512eb2416032602ef9861c Mon Sep 17 00:00:00 2001
From: Mel Henning <mhenning@darkrefraction.com>
Date: Wed, 1 Oct 2025 19:37:15 -0400
Subject: [PATCH 11/15] nvk: INVALIDATE_SHADER_CACHES on most recent subc

This should be a bit faster.
---
 src/nouveau/vulkan/nvk_cmd_buffer.c | 6 +-----
 1 file changed, 1 insertion(+), 5 deletions(-)

diff --git a/src/nouveau/vulkan/nvk_cmd_buffer.c b/src/nouveau/vulkan/nvk_cmd_buffer.c
index 4e224dff6177b..52d24e255ea7a 100644
--- a/src/nouveau/vulkan/nvk_cmd_buffer.c
+++ b/src/nouveau/vulkan/nvk_cmd_buffer.c
@@ -510,10 +510,6 @@ nvk_cmd_flush_wait_dep(struct nvk_cmd_buffer *cmd,
                        const VkDependencyInfo *dep,
                        bool wait)
 {
-   VkQueueFlags queue_flags = nvk_cmd_buffer_queue_flags(cmd);
-   enum nvkmd_engines engines =
-      nvk_queue_engines_from_queue_flags(queue_flags);
-
    enum nvk_barrier barriers = 0;
 
    for (uint32_t i = 0; i < dep->memoryBarrierCount; i++) {
@@ -541,7 +537,7 @@ nvk_cmd_flush_wait_dep(struct nvk_cmd_buffer *cmd,
 
    if (barriers & NVK_BARRIER_FLUSH_SHADER_DATA) {
       /* This is also implicitly a WFI */
-      if (engines & NVKMD_ENGINE_3D) {
+      if (nvk_cmd_buffer_last_subchannel(cmd) == SUBC_NVA097) {
          P_IMMD(p, NVA097, INVALIDATE_SHADER_CACHES, {
             .data = DATA_TRUE,
             .flush_data = FLUSH_DATA_TRUE,
-- 
GitLab


From 6bfae651fe1b7328d89d110a966e1ce7e56d8149 Mon Sep 17 00:00:00 2001
From: Mel Henning <mhenning@darkrefraction.com>
Date: Wed, 1 Oct 2025 19:51:28 -0400
Subject: [PATCH 12/15] nvk: WFI on the most recent subc

This should be a bit faster. It also matches what the proprietary driver
generates, based on the reverse engineering done here:
https://gitlab.freedesktop.org/mhenning/re/-/tree/main/vk_test_overlap_exec
---
 src/nouveau/vulkan/nvk_cmd_buffer.c | 40 +++++++++++++++++++++++++----
 1 file changed, 35 insertions(+), 5 deletions(-)

diff --git a/src/nouveau/vulkan/nvk_cmd_buffer.c b/src/nouveau/vulkan/nvk_cmd_buffer.c
index 52d24e255ea7a..3a4e7862966c5 100644
--- a/src/nouveau/vulkan/nvk_cmd_buffer.c
+++ b/src/nouveau/vulkan/nvk_cmd_buffer.c
@@ -533,9 +533,9 @@ nvk_cmd_flush_wait_dep(struct nvk_cmd_buffer *cmd,
    if (!barriers)
       return;
 
-   struct nv_push *p = nvk_cmd_buffer_push(cmd, 2);
-
    if (barriers & NVK_BARRIER_FLUSH_SHADER_DATA) {
+      struct nv_push *p = nvk_cmd_buffer_push(cmd, 2);
+
       /* This is also implicitly a WFI */
       if (nvk_cmd_buffer_last_subchannel(cmd) == SUBC_NVA097) {
          P_IMMD(p, NVA097, INVALIDATE_SHADER_CACHES, {
@@ -548,14 +548,44 @@ nvk_cmd_flush_wait_dep(struct nvk_cmd_buffer *cmd,
             .flush_data = FLUSH_DATA_TRUE,
          });
       }
-   } else if (barriers & NVK_BARRIER_WFI) {
+   } else if ((barriers & NVK_BARRIER_WFI) && wait) {
       /* If this comes from a vkCmdSetEvent, we don't need to wait
        *
        * We only need to WFI on a single channel. The others will implicitly get
        * a WFI from the channel switch.
        */
-      if (wait)
-         P_IMMD(p, NVA097, WAIT_FOR_IDLE, 0);
+      switch (nvk_cmd_buffer_last_subchannel(cmd)) {
+      case SUBC_NV9097: {
+         struct nv_push *p = nvk_cmd_buffer_push(cmd, 2);
+         P_IMMD(p, NV9097, WAIT_FOR_IDLE, 0);
+         break;
+      }
+      case SUBC_NV90C0: {
+         struct nv_push *p = nvk_cmd_buffer_push(cmd, 2);
+         P_IMMD(p, NVA0C0, WAIT_FOR_IDLE, 0);
+         break;
+      }
+      default:
+         assert(!"Unknown subc");
+         /* Fall through */
+      case SUBC_NV90B5: {
+         struct nv_push *p = nvk_cmd_buffer_push(cmd, 5);
+         P_MTHD(p, NV90B5, LINE_LENGTH_IN);
+         P_NV90B5_LINE_LENGTH_IN(p, 0);
+         P_NV90B5_LINE_COUNT(p, 0);
+
+         P_IMMD(p, NV90B5, LAUNCH_DMA, {
+            .data_transfer_type = DATA_TRANSFER_TYPE_NON_PIPELINED,
+            .multi_line_enable = false,
+            .flush_enable = FLUSH_ENABLE_TRUE,
+            /* Note: FLUSH_TYPE=SYS implicitly for NVC3B5+ */
+            .src_memory_layout = SRC_MEMORY_LAYOUT_PITCH,
+            .dst_memory_layout = DST_MEMORY_LAYOUT_PITCH,
+            .remap_enable = REMAP_ENABLE_TRUE,
+         });
+         break;
+      }
+      }
    }
 }
 
-- 
GitLab


From a5c6fa4384ea90642b3cf34913444bc5d9929da9 Mon Sep 17 00:00:00 2001
From: Mel Henning <mhenning@darkrefraction.com>
Date: Wed, 1 Oct 2025 20:11:21 -0400
Subject: [PATCH 13/15] nvk/cmd_copy: Use PIPELINED for user transfers

Vulkan requires applications to insert any necessary pipeline barriers.
---
 src/nouveau/vulkan/nvk_cmd_copy.c | 6 +++---
 1 file changed, 3 insertions(+), 3 deletions(-)

diff --git a/src/nouveau/vulkan/nvk_cmd_copy.c b/src/nouveau/vulkan/nvk_cmd_copy.c
index c4ea93fd3963f..5382d1b71d83c 100644
--- a/src/nouveau/vulkan/nvk_cmd_copy.c
+++ b/src/nouveau/vulkan/nvk_cmd_copy.c
@@ -398,7 +398,7 @@ nvk_CmdCopyBuffer2(VkCommandBuffer commandBuffer,
          P_NV90B5_LINE_COUNT(p, 1);
 
          P_IMMD(p, NV90B5, LAUNCH_DMA, {
-                .data_transfer_type = DATA_TRANSFER_TYPE_NON_PIPELINED,
+                .data_transfer_type = DATA_TRANSFER_TYPE_PIPELINED,
                 .multi_line_enable = MULTI_LINE_ENABLE_TRUE,
                 .flush_enable = FLUSH_ENABLE_TRUE,
                 .src_memory_layout = SRC_MEMORY_LAYOUT_PITCH,
@@ -941,7 +941,7 @@ nvk_CmdFillBuffer(VkCommandBuffer commandBuffer,
       P_NV90B5_LINE_COUNT(p, height);
 
       P_IMMD(p, NV90B5, LAUNCH_DMA, {
-         .data_transfer_type = DATA_TRANSFER_TYPE_NON_PIPELINED,
+         .data_transfer_type = DATA_TRANSFER_TYPE_PIPELINED,
          .multi_line_enable = height > 1,
          .flush_enable = FLUSH_ENABLE_TRUE,
          .src_memory_layout = SRC_MEMORY_LAYOUT_PITCH,
@@ -982,7 +982,7 @@ nvk_CmdUpdateBuffer(VkCommandBuffer commandBuffer,
    P_NV90B5_LINE_COUNT(p, 1);
 
    P_IMMD(p, NV90B5, LAUNCH_DMA, {
-      .data_transfer_type = DATA_TRANSFER_TYPE_NON_PIPELINED,
+      .data_transfer_type = DATA_TRANSFER_TYPE_PIPELINED,
       .multi_line_enable = MULTI_LINE_ENABLE_TRUE,
       .flush_enable = FLUSH_ENABLE_TRUE,
       .src_memory_layout = SRC_MEMORY_LAYOUT_PITCH,
-- 
GitLab


From 8d20c05e8d0857ac1082a2f0c01ed57523e9ab67 Mon Sep 17 00:00:00 2001
From: Mel Henning <mhenning@darkrefraction.com>
Date: Wed, 1 Oct 2025 20:20:44 -0400
Subject: [PATCH 14/15] nvk/cmd_copy: Pipeline user copy_rect operations

---
 src/nouveau/vulkan/nvk_cmd_copy.c | 30 ++++++++++++++++++++----------
 1 file changed, 20 insertions(+), 10 deletions(-)

diff --git a/src/nouveau/vulkan/nvk_cmd_copy.c b/src/nouveau/vulkan/nvk_cmd_copy.c
index 5382d1b71d83c..09028afc6df92 100644
--- a/src/nouveau/vulkan/nvk_cmd_copy.c
+++ b/src/nouveau/vulkan/nvk_cmd_copy.c
@@ -186,7 +186,9 @@ nil_to_nvcab5_gob_type(enum nil_gob_type gob_type)
 }
 
 static void
-nouveau_copy_rect(struct nvk_cmd_buffer *cmd, struct nouveau_copy *copy)
+nouveau_copy_rect(struct nvk_cmd_buffer *cmd,
+                  struct nouveau_copy *copy,
+                  uint8_t data_transfer_type)
 {
    uint32_t src_bw, dst_bw;
    if (copy->remap.comp_size > 0) {
@@ -357,7 +359,7 @@ nouveau_copy_rect(struct nvk_cmd_buffer *cmd, struct nouveau_copy *copy)
       }
 
       P_IMMD(p, NV90B5, LAUNCH_DMA, {
-         .data_transfer_type = DATA_TRANSFER_TYPE_NON_PIPELINED,
+         .data_transfer_type = data_transfer_type,
          .multi_line_enable = MULTI_LINE_ENABLE_TRUE,
          .flush_enable = FLUSH_ENABLE_TRUE,
          .src_memory_layout = src_layout,
@@ -515,9 +517,11 @@ nvk_CmdCopyBufferToImage2(VkCommandBuffer commandBuffer,
                                     &region->imageSubresource);
       }
 
-      nouveau_copy_rect(cmd, &copy);
+      nouveau_copy_rect(cmd, &copy,
+                        NV90B5_LAUNCH_DMA_DATA_TRANSFER_TYPE_PIPELINED);
       if (copy2.extent_el.width > 0)
-         nouveau_copy_rect(cmd, &copy2);
+         nouveau_copy_rect(cmd, &copy2,
+                           NV90B5_LAUNCH_DMA_DATA_TRANSFER_TYPE_NON_PIPELINED);
 
       vk_foreach_struct_const(ext, region->pNext) {
          switch (ext->sType) {
@@ -640,9 +644,11 @@ nvk_CmdCopyImageToBuffer2(VkCommandBuffer commandBuffer,
                                     &region->imageSubresource);
       }
 
-      nouveau_copy_rect(cmd, &copy);
+      nouveau_copy_rect(cmd, &copy,
+                        NV90B5_LAUNCH_DMA_DATA_TRANSFER_TYPE_PIPELINED);
       if (copy2.extent_el.width > 0)
-         nouveau_copy_rect(cmd, &copy2);
+         nouveau_copy_rect(cmd, &copy2,
+                           NV90B5_LAUNCH_DMA_DATA_TRANSFER_TYPE_NON_PIPELINED);
 
       vk_foreach_struct_const(ext, region->pNext) {
          switch (ext->sType) {
@@ -708,7 +714,8 @@ nvk_linear_render_copy(struct nvk_cmd_buffer *cmd,
 
    assert(src_plane->nil.format.p_format == dst_plane->nil.format.p_format);
    copy.remap = nouveau_copy_remap_format(src_plane->nil.format.p_format);
-   nouveau_copy_rect(cmd, &copy);
+   nouveau_copy_rect(cmd, &copy,
+                     NV90B5_LAUNCH_DMA_DATA_TRANSFER_TYPE_NON_PIPELINED);
 }
 
 static void
@@ -823,7 +830,8 @@ nvk_CmdCopyImage2(VkCommandBuffer commandBuffer,
                .extent_el = nil_extent4d_px_to_el(extent4d_px, format,
                                                   sample_layout),
             };
-            nouveau_copy_rect(cmd, &copy);
+            nouveau_copy_rect(cmd, &copy,
+                              NV90B5_LAUNCH_DMA_DATA_TRANSFER_TYPE_PIPELINED);
          }
       } else {
          uint8_t src_plane = nvk_image_aspects_to_plane(src, src_aspects);
@@ -876,9 +884,11 @@ nvk_CmdCopyImage2(VkCommandBuffer commandBuffer,
             copy.remap = nouveau_copy_remap_format(src_format.p_format);
          }
 
-         nouveau_copy_rect(cmd, &copy);
+         nouveau_copy_rect(cmd, &copy,
+                           NV90B5_LAUNCH_DMA_DATA_TRANSFER_TYPE_PIPELINED);
          if (copy2.extent_el.width > 0)
-            nouveau_copy_rect(cmd, &copy2);
+            nouveau_copy_rect(cmd, &copy2,
+                              NV90B5_LAUNCH_DMA_DATA_TRANSFER_TYPE_NON_PIPELINED);
       }
    }
 }
-- 
GitLab


From d0dff20bdcd239ea0f3e795284fdde0549f553e5 Mon Sep 17 00:00:00 2001
From: Mel Henning <mhenning@darkrefraction.com>
Date: Fri, 15 Aug 2025 19:55:52 -0400
Subject: [PATCH 15/15] nvk: Reduce subc switches with events

---
 src/nouveau/vulkan/nvk_event.c | 79 ++++++++++++++++++++++------------
 1 file changed, 51 insertions(+), 28 deletions(-)

diff --git a/src/nouveau/vulkan/nvk_event.c b/src/nouveau/vulkan/nvk_event.c
index bf665ab6720e3..d6ad820ebb395 100644
--- a/src/nouveau/vulkan/nvk_event.c
+++ b/src/nouveau/vulkan/nvk_event.c
@@ -11,6 +11,8 @@
 
 #include "nv_push_cl906f.h"
 #include "nv_push_cl9097.h"
+#include "nv_push_cl90b5.h"
+#include "nv_push_cl90c0.h"
 
 #define NVK_EVENT_MEM_SIZE sizeof(VkResult)
 
@@ -148,10 +150,6 @@ vk_stage_flags_to_nv9097_pipeline_location(VkPipelineStageFlags2 flags)
                         VK_PIPELINE_STAGE_2_HOST_BIT |
                         VK_PIPELINE_STAGE_2_CONDITIONAL_RENDERING_BIT_EXT);
 
-   /* TODO: Doing this on 3D will likely cause a WFI which is probably ok but,
-    * if we tracked which subchannel we've used most recently, we can probably
-    * do better than that.
-    */
    clear_bits64(&flags, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
 
    assert(flags == 0);
@@ -159,6 +157,52 @@ vk_stage_flags_to_nv9097_pipeline_location(VkPipelineStageFlags2 flags)
    return NV9097_SET_REPORT_SEMAPHORE_D_PIPELINE_LOCATION_NONE;
 }
 
+static void
+nvk_event_report_semaphore(struct nvk_cmd_buffer *cmd,
+                           VkPipelineStageFlags2 stages,
+                           uint64_t addr, uint32_t value)
+{
+   uint8_t subc = nvk_cmd_buffer_last_subchannel(cmd);
+   if (subc == SUBC_NV9097) {
+      struct nv_push *p = nvk_cmd_buffer_push(cmd, 5);
+      P_MTHD(p, NV9097, SET_REPORT_SEMAPHORE_A);
+      P_NV9097_SET_REPORT_SEMAPHORE_A(p, addr >> 32);
+      P_NV9097_SET_REPORT_SEMAPHORE_B(p, addr);
+      P_NV9097_SET_REPORT_SEMAPHORE_C(p, value);
+      P_NV9097_SET_REPORT_SEMAPHORE_D(p, {
+         .operation = OPERATION_RELEASE,
+         .release = RELEASE_AFTER_ALL_PRECEEDING_WRITES_COMPLETE,
+         .pipeline_location = vk_stage_flags_to_nv9097_pipeline_location(stages),
+         .structure_size = STRUCTURE_SIZE_ONE_WORD,
+      });
+   } else if (subc == SUBC_NV90C0) {
+      struct nv_push *p = nvk_cmd_buffer_push(cmd, 5);
+      P_MTHD(p, NV90C0, SET_REPORT_SEMAPHORE_A);
+      P_NV90C0_SET_REPORT_SEMAPHORE_A(p, addr >> 32);
+      P_NV90C0_SET_REPORT_SEMAPHORE_B(p, addr);
+      P_NV90C0_SET_REPORT_SEMAPHORE_C(p, value);
+      P_NV90C0_SET_REPORT_SEMAPHORE_D(p, {
+         .operation = OPERATION_RELEASE,
+         .structure_size = STRUCTURE_SIZE_ONE_WORD,
+      });
+   } else {
+      assert(subc == SUBC_NV90B5);
+      struct nv_push *p = nvk_cmd_buffer_push(cmd, 6);
+
+      P_MTHD(p, NV90B5, SET_SEMAPHORE_A);
+      P_NV90B5_SET_SEMAPHORE_A(p, addr >> 32);
+      P_NV90B5_SET_SEMAPHORE_B(p, addr);
+      P_NV90B5_SET_SEMAPHORE_PAYLOAD(p, value);
+
+      P_IMMD(p, NV90B5, LAUNCH_DMA, {
+         .data_transfer_type = DATA_TRANSFER_TYPE_NONE,
+         .semaphore_type = SEMAPHORE_TYPE_RELEASE_ONE_WORD_SEMAPHORE,
+         .flush_enable = FLUSH_ENABLE_TRUE,
+         /* Note: FLUSH_TYPE=SYS implicitly for NVC3B5+ */
+      });
+   }
+}
+
 VKAPI_ATTR void VKAPI_CALL
 nvk_CmdSetEvent2(VkCommandBuffer commandBuffer,
                  VkEvent _event,
@@ -177,17 +221,7 @@ nvk_CmdSetEvent2(VkCommandBuffer commandBuffer,
    for (uint32_t i = 0; i < pDependencyInfo->imageMemoryBarrierCount; i++)
       stages |= pDependencyInfo->pImageMemoryBarriers[i].srcStageMask;
 
-   struct nv_push *p = nvk_cmd_buffer_push(cmd, 5);
-   P_MTHD(p, NV9097, SET_REPORT_SEMAPHORE_A);
-   P_NV9097_SET_REPORT_SEMAPHORE_A(p, event->addr >> 32);
-   P_NV9097_SET_REPORT_SEMAPHORE_B(p, event->addr);
-   P_NV9097_SET_REPORT_SEMAPHORE_C(p, VK_EVENT_SET);
-   P_NV9097_SET_REPORT_SEMAPHORE_D(p, {
-      .operation = OPERATION_RELEASE,
-      .release = RELEASE_AFTER_ALL_PRECEEDING_WRITES_COMPLETE,
-      .pipeline_location = vk_stage_flags_to_nv9097_pipeline_location(stages),
-      .structure_size = STRUCTURE_SIZE_ONE_WORD,
-   });
+   nvk_event_report_semaphore(cmd, stages, event->addr, VK_EVENT_SET);
 }
 
 VKAPI_ATTR void VKAPI_CALL
@@ -198,18 +232,7 @@ nvk_CmdResetEvent2(VkCommandBuffer commandBuffer,
    VK_FROM_HANDLE(nvk_cmd_buffer, cmd, commandBuffer);
    VK_FROM_HANDLE(nvk_event, event, _event);
 
-   struct nv_push *p = nvk_cmd_buffer_push(cmd, 5);
-   P_MTHD(p, NV9097, SET_REPORT_SEMAPHORE_A);
-   P_NV9097_SET_REPORT_SEMAPHORE_A(p, event->addr >> 32);
-   P_NV9097_SET_REPORT_SEMAPHORE_B(p, event->addr);
-   P_NV9097_SET_REPORT_SEMAPHORE_C(p, VK_EVENT_RESET);
-   P_NV9097_SET_REPORT_SEMAPHORE_D(p, {
-      .operation = OPERATION_RELEASE,
-      .release = RELEASE_AFTER_ALL_PRECEEDING_WRITES_COMPLETE,
-      .pipeline_location =
-         vk_stage_flags_to_nv9097_pipeline_location(stageMask),
-      .structure_size = STRUCTURE_SIZE_ONE_WORD,
-   });
+   nvk_event_report_semaphore(cmd, stageMask, event->addr, VK_EVENT_RESET);
 }
 
 VKAPI_ATTR void VKAPI_CALL
@@ -224,7 +247,7 @@ nvk_CmdWaitEvents2(VkCommandBuffer commandBuffer,
       VK_FROM_HANDLE(nvk_event, event, pEvents[i]);
 
       struct nv_push *p = nvk_cmd_buffer_push(cmd, 5);
-      __push_mthd(p, SUBC_NV9097, NV906F_SEMAPHOREA);
+      __push_mthd(p, nvk_cmd_buffer_last_subchannel(cmd), NV906F_SEMAPHOREA);
       P_NV906F_SEMAPHOREA(p, event->addr >> 32);
       P_NV906F_SEMAPHOREB(p, (event->addr & UINT32_MAX) >> 2);
       P_NV906F_SEMAPHOREC(p, VK_EVENT_SET);
-- 
GitLab

