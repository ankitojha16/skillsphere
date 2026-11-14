"""
SkillSphere Career Studio — Career Roadmap Generator.
Generates and synchronizes personalized, milestone-driven learning roadmaps
connected directly to SkillSphere courses, challenges, and portfolio projects.
Preserves student progress and prevents overwriting of completed milestones.
"""

import json
import logging
from typing import Optional, List
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

from roadmaps.models import LearningRoadmap, RoadmapMilestone
from careers.models import CareerTrack, StudentCareerGoal

logger = logging.getLogger('skillsphere.careers')


class CareerRoadmapGenerator:
    """
    Generates dynamic, interactive learning roadmaps for students based on their
    selected CareerTrack and estimated completion timeline.
    """

    @classmethod
    def generate_or_sync_roadmap(
        cls,
        user: User,
        track: CareerTrack,
        timeline_months: int = 6
    ) -> LearningRoadmap:
        """
        Creates or updates a LearningRoadmap for the student mapped to the chosen track.
        Never overwrites already-completed milestones.
        """
        daily_time = "1.5 hours/day" if timeline_months <= 3 else "1 hour/day"
        duration_label = f"{timeline_months} months"

        with transaction.atomic():
            roadmap, created = LearningRoadmap.objects.get_or_create(
                user=user,
                target_skill=track.title,
                defaults={
                    'title': f"{track.title} Professional Roadmap",
                    'current_level': track.difficulty_level,
                    'career_goal': track.title,
                    'daily_time': daily_time,
                    'duration': duration_label,
                }
            )

            if not created:
                roadmap.career_goal = track.title
                roadmap.duration = duration_label
                roadmap.save(update_fields=['career_goal', 'duration', 'updated_at'])

            # Synchronize milestones from curated track definitions
            track_milestones = track.learning_milestones or []
            existing_milestones = {m.milestone_order: m for m in roadmap.milestones.all()}

            for index, item in enumerate(track_milestones, start=1):
                title = item.get('title', f"Phase {index}: Mastery")
                description = item.get('description', '')
                topics = item.get('topics', [])
                mini_project = item.get('mini_project', '')
                estimated_weeks = item.get('weeks', max(2, int(timeline_months * 4 / max(1, len(track_milestones)))))

                if index in existing_milestones:
                    ms = existing_milestones[index]
                    # Only update description/topics if the milestone is not yet completed
                    if not ms.is_completed:
                        ms.title = title
                        ms.description = description
                        ms.topics_json = json.dumps(topics)
                        ms.mini_project = mini_project
                        ms.estimated_weeks = estimated_weeks
                        ms.save()
                else:
                    RoadmapMilestone.objects.create(
                        roadmap=roadmap,
                        title=title,
                        description=description,
                        topics_json=json.dumps(topics),
                        mini_project=mini_project,
                        milestone_order=index,
                        estimated_weeks=estimated_weeks,
                        is_completed=False,
                    )

        return roadmap

    @classmethod
    def reorder_milestones(cls, roadmap: LearningRoadmap, ordered_ids: List[int]) -> bool:
        """
        Reorders milestones based on student customization.
        """
        with transaction.atomic():
            milestones = {m.id: m for m in roadmap.milestones.filter(id__in=ordered_ids)}
            for order, m_id in enumerate(ordered_ids, start=1):
                if m_id in milestones:
                    m = milestones[m_id]
                    m.milestone_order = order
                    m.save(update_fields=['milestone_order'])
        return True

    @classmethod
    def toggle_milestone_completion(cls, milestone_id: int, user: User) -> Optional[RoadmapMilestone]:
        """
        Toggles completion state of a milestone, validating ownership.
        """
        try:
            milestone = RoadmapMilestone.objects.select_related('roadmap').get(
                id=milestone_id,
                roadmap__user=user
            )
            milestone.is_completed = not milestone.is_completed
            milestone.completed_at = timezone.now() if milestone.is_completed else None
            milestone.save(update_fields=['is_completed', 'completed_at'])
            return milestone
        except RoadmapMilestone.DoesNotExist:
            return None
