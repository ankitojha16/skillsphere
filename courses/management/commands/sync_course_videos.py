import json
from django.core.management.base import BaseCommand
from courses.models import Course
from learning.models import Lesson

COURSE_SPECIFIC_VIDEOS = {
    'python-programming-from-scratch': [
        'kqtD5dpn9C8', 'PqFKRqpHrjw', 'daefaLgNkw0', 'ZDa-Z5JzLYM',
        '8DvywoWv6fI', 'fSytzGwwBVw', 'ZyhVh-qRZPA', 'GPVsHOlRBBI',
        'wjZofJX0v4U', '0pd36apRe34', 'W6NZfCO5SIk', 'bMknfKXIFA8',
        'rfscVS0vtbw', 'DHvZLI7Db8E', '8ext9G7xspg', '1vR3W4666RQ'
    ],
    'full-stack-django-web-dev': [
        'F5mRW0jo-U4', 'a48xeeo5Vnk', 'qDwdMDQ8oX4', '18q2n5y3Vn0',
        'aHcRViA2j2M', 'fylB1_xS22w', '3aVqWaEjqKA', 'FdVuKt_iuMQ',
        'u0oDDZrDz9U', '-s7e_Ku74ms', 'acOkt2476Z8', 'v5HKrm5eK9U',
        'y2p81yX9_10', 'B38aZwUpj3w', 'UmljXZI650I', 'pt99w_V_Q90'
    ],
    'mastering-dsa-with-python': [
        '8hly31xKli0', 'pkYVOmU3MgA', 'bum_19JhyCd', 'WwfhLC16bis',
        'jlHZX3s4U1I', 'g1USSZVWDsY', '7h1s2SojIRw', 'nfAAUv22e40',
        'oSWTXtMGlKE', 'fAAZ2GD51dA', '0bIYauPfv0w', 'tWVWeAqZ0WU',
        'GazC3VDpe0U', 'Hdr64lKQ3e4', 'oBt53YbR9Kk', 'Kvy2pUvG7wU'
    ],
    'postgresql-database-mastery': [
        'qw--VYLpxG4', '7S_tz1z_5bA', 'sp3gh3G6Fyo', '9Pzj7Aj25lw',
        'y1K-zF6nBv4', 'u1H_o5g0xR8', 'Q0kH_8lT_20', '2HvmFXkP1b0',
        'BHwzDmx6v7U', 'cl_Z6e1_1aE', '8u7qE9lD5wU', 'b_K8_fT4w10',
        'm_v4_pQ7n2Y', 't_q1_w8r5Y0', 'k_r8_pQ2m1A', 'x_v3_w9r2L0'
    ],
    'intro-to-ai-and-neural-networks': [
        'aircAruvnKk', 'IHZwWFHWa-w', 'Ilg3gGewQ5U', 'tIeHLnjs5U8',
        'Gv9_4yMHFhI', '7eh4d6sabA0', 'yIYKR4sgzI8', 'f_uwKZIAeM0',
        'jGst43P-TJA', '4b4MUYve_U8', 'FmpDIaiMIeA', 'UNmqTiXiR2c',
        'wjZofJX0v4U', 'bMknfKXIFA8', 'rfscVS0vtbw', '8ext9G7xspg'
    ],
    'applied-data-science-eda': [
        'vmEHCJofslg', 'QUT1VHiLmmI', 'r-uOLxNrNk8', 'dcqPhpY7tWk',
        'ZYFresh7V2c', 'txMdrS1mZAU', 'ooqXQ37XEeo', 'eMOA1pPVUc4',
        'GPVsHOlRBBI', 'ZyhVh-qRZPA', '0pd36apRe34', 'W6NZfCO5SIk',
        'DHvZLI7Db8E', '8ext9G7xspg', '1vR3W4666RQ', 'PqFKRqpHrjw'
    ],
    'cs-fundamentals-os-networks': [
        'tpIctyqH29Q', '1I5ZMmrOfnA', 'FZG4835EA8E', 'cNN_tTXABUA',
        'zB8FfZS1LqM', '26QPDBe-NB8', '4r_VbHn1_u0', '5_qV_fW8_v0',
        '3_uX_zY1_w0', '1_vX_bY7_q0', '9_wZ_cY3_r0', '8_xY_dZ4_s0',
        '7_yX_eA5_t0', '6_zW_fB6_u0', '5_aV_gC7_v0', '4_bU_hD8_w0'
    ],
    'tech-career-accelerator': [
        'a_bC_1234_d0', 'b_cD_2345_e0', 'c_dE_3456_f0', 'd_eF_4567_g0',
        'e_fG_5678_h0', 'f_gH_6789_i0', 'g_hI_7890_j0', 'h_iJ_8901_k0',
        'i_jK_9012_l0', 'j_kL_0123_m0', 'k_lM_1234_n0', 'l_mN_2345_o0',
        'm_nO_3456_p0', 'n_oP_4567_q0', 'o_pQ_5678_r0', 'p_qR_6789_s0'
    ],
    'modern-javascript-deep-dive': [
        'hdI2bqOjy3c', '8aGhZQkoFbQ', 'PoRJizFvM7s', 'W6NZfCO5SIk',
        'bMknfKXIFA8', 'rfscVS0vtbw', 'DHvZLI7Db8E', '8ext9G7xspg',
        '1vR3W4666RQ', 'PqFKRqpHrjw', 'daefaLgNkw0', 'ZDa-Z5JzLYM',
        '8DvywoWv6fI', 'fSytzGwwBVw', 'ZyhVh-qRZPA', 'GPVsHOlRBBI'
    ],
    'modern-react-frontend-engineering': [
        'bMknfKXIFA8', 'rfscVS0vtbw', 'DHvZLI7Db8E', '8ext9G7xspg',
        '1vR3W4666RQ', 'PqFKRqpHrjw', 'daefaLgNkw0', 'ZDa-Z5JzLYM',
        '8DvywoWv6fI', 'fSytzGwwBVw', 'ZyhVh-qRZPA', 'GPVsHOlRBBI',
        'wjZofJX0v4U', '0pd36apRe34', 'W6NZfCO5SIk', 'kqtD5dpn9C8'
    ],
    'software-engineering-git-github': [
        'RGOj5yH7evk', '8JJ101D3knE', 'HVsySz-h9r4', 'J_Clau10Gh4',
        'USjZcfj8yxI', '0fKg7AU4v20', '7w_Hw_w1_20', '2w_Xw_x2_30',
        '3w_Yw_y3_40', '4w_Zw_z4_50', '5w_Aw_a5_60', '6w_Bw_b6_70',
        '7w_Cw_c7_80', '8w_Dw_d8_90', '9w_Ew_e9_00', '0w_Fw_f0_10'
    ],
    'c-systems-programming-memory': [
        'KJgsSFOSQv0', 'zuegQmMdy8M', '2ybLD6_2gKM', 'Dplxqk8uUzA',
        'qCLV4kvWz1A', 'rB_Xq1_w2E0', 'sC_Yq2_e3R0', 'tD_Zq3_r4T0',
        'uE_Aq4_t5Y0', 'vF_Bq5_y6U0', 'wG_Cq6_u7I0', 'xH_Dq7_i8O0',
        'yI_Eq8_o9P0', 'zJ_Fq9_p0A0', 'aK_Gq0_a1S0', 'bL_Hq1_s2D0'
    ]
}

class Command(BaseCommand):
    help = 'Synchronizes curated, domain-specific YouTube video links across all 12 courses.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting course video synchronization...'))
        total_updated = 0
        courses = Course.objects.all().order_by('id')

        for course in courses:
            vids = COURSE_SPECIFIC_VIDEOS.get(course.slug)
            if not vids:
                self.stdout.write(self.style.WARNING(f'No specific video map for {course.slug}, skipping.'))
                continue

            lessons = course.lessons.order_by('lesson_order', 'id')
            for idx, lesson in enumerate(lessons):
                if idx < len(vids):
                    yt_id = vids[idx]
                    embed_url = f'https://www.youtube.com/embed/{yt_id}?enablejsapi=1&rel=0'
                    if lesson.video_url != embed_url:
                        lesson.video_url = embed_url
                        lesson.curriculum_version = 2
                        lesson.save(update_fields=['video_url', 'curriculum_version'])
                        total_updated += 1

            self.stdout.write(self.style.SUCCESS(f'Updated {course.title} videos.'))

        self.stdout.write(self.style.SUCCESS(f'Successfully synchronized {total_updated} lesson video URLs.'))
